import hashlib
import re
import time
import uuid
from decimal import Decimal

from boto3.dynamodb.conditions import Key


def _now_ms():
    return int(time.time() * 1000)


def _normalise(text):
    value = re.sub(r"\s+", " ", str(text or "").strip().casefold())
    if not value or len(value) > 300:
        raise ValueError("Invalid term")
    return value


def _ddb_safe(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {str(k): _ddb_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_ddb_safe(v) for v in value]
    return value


def _plain(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _compact_profile(item):
    if not item:
        return None
    keep = {
        "entityId", "label", "entityType", "aliases", "attributes", "truthDomain",
        "provenance", "sourceRef", "observation", "revision", "createdAt", "updatedAt",
        "canonStatus",
    }
    return _plain({k: v for k, v in item.items() if k in keep})


class DynamoRelicStore:
    def __init__(self, table, actor):
        self.table = table
        actor = str(actor or "").strip()
        if not actor:
            raise ValueError("Authenticated actor required")
        self.actor = actor

    def _entity_pk(self, entity_id):
        return f"USER#{self.actor}#ENTITY#{entity_id}"

    def _alias_pk(self, term):
        digest = hashlib.sha256(_normalise(term).encode("utf-8")).hexdigest()
        return f"USER#{self.actor}#ALIAS#{digest}"

    def _profile(self, entity_id):
        item = self.table.get_item(
            Key={"pk": self._entity_pk(entity_id), "sk": "PROFILE"},
            ConsistentRead=True,
        ).get("Item")
        return item

    def exists(self, entity_id):
        return self._profile(str(entity_id)) is not None

    def _write_alias(self, entity_id, alias, label):
        normalized = _normalise(alias)
        self.table.put_item(Item={
            "pk": self._alias_pk(normalized),
            "sk": f"ENTITY#{entity_id}",
            "entityId": entity_id,
            "label": label,
            "normalized": normalized,
            "actor": self.actor,
            "updatedAt": _now_ms(),
        })

    def identify(self, query, limit=10):
        normalized = _normalise(query)
        result = self.table.query(
            KeyConditionExpression=Key("pk").eq(self._alias_pk(normalized)),
            Limit=max(1, min(int(limit), 20)),
            ConsistentRead=True,
        )
        matches = []
        for alias_item in result.get("Items", []):
            profile = self._profile(alias_item.get("entityId"))
            compact = _compact_profile(profile)
            if compact:
                compact["matchedTerm"] = query
                compact["matchKind"] = "label-or-alias"
                matches.append(compact)
        return {
            "query": query,
            "normalized": normalized,
            "matches": matches[:limit],
            "identityRule": "representation-does-not-prove-identity",
        }

    def _relationships(self, entity_id, limit=100):
        result = self.table.query(
            KeyConditionExpression=Key("pk").eq(self._entity_pk(entity_id)) & Key("sk").begins_with("REL#"),
            Limit=max(1, min(int(limit), 100)),
            ScanIndexForward=False,
        )
        return [_plain(x) for x in result.get("Items", [])]

    def _inbound(self, entity_id, limit=100):
        result = self.table.query(
            KeyConditionExpression=Key("pk").eq(self._entity_pk(entity_id)) & Key("sk").begins_with("IN#"),
            Limit=max(1, min(int(limit), 100)),
            ScanIndexForward=False,
        )
        return [_plain(x) for x in result.get("Items", [])]

    def _events(self, entity_id, limit=25):
        result = self.table.query(
            KeyConditionExpression=Key("pk").eq(self._entity_pk(entity_id)) & Key("sk").begins_with("EVENT#"),
            Limit=max(1, min(int(limit), 50)),
            ScanIndexForward=False,
        )
        return [_plain(x) for x in result.get("Items", [])]

    def observe(self, entity_id, include_events=False, relationship_depth=1):
        profile = self._profile(entity_id)
        if not profile:
            raise ValueError("Entity not found")
        payload = {
            "entity": _compact_profile(profile),
            "relationships": self._relationships(entity_id),
            "inboundRelationships": self._inbound(entity_id),
            "canonStatus": "non-canonical-relic-memory",
            "worldTruthChanged": False,
        }
        if include_events:
            payload["events"] = self._events(entity_id)
        depth = max(0, min(int(relationship_depth), 3))
        if depth:
            related_ids = []
            for rel in payload["relationships"]:
                related_ids.append(rel.get("targetId"))
            for rel in payload["inboundRelationships"]:
                related_ids.append(rel.get("sourceId"))
            seen = {entity_id}
            related = []
            frontier = [(rid, 1) for rid in related_ids if rid]
            while frontier and len(related) < 40:
                rid, level = frontier.pop(0)
                if rid in seen or level > depth:
                    continue
                seen.add(rid)
                rp = self._profile(rid)
                if not rp:
                    continue
                related.append(_compact_profile(rp))
                if level < depth:
                    for edge in self._relationships(rid, 25):
                        target = edge.get("targetId")
                        if target and target not in seen:
                            frontier.append((target, level + 1))
            payload["relatedEntities"] = related
        return payload

    def context(self, terms, relationship_depth=1, max_entities=20):
        max_entities = max(1, min(int(max_entities), 40))
        resolved = []
        entities = []
        seen = set()
        for term in terms[:20]:
            result = self.identify(term, 5)
            ids = [m.get("entityId") for m in result.get("matches", []) if m.get("entityId")]
            resolved.append({"term": term, "entityIds": ids})
            for entity_id in ids:
                if entity_id in seen or len(entities) >= max_entities:
                    continue
                seen.add(entity_id)
                entities.append(self.observe(entity_id, False, relationship_depth))
        return {
            "purpose": "compact-persistent-context",
            "resolvedTerms": resolved,
            "entities": entities,
            "entityCount": len(entities),
            "truthBoundary": "ReLiC memory; not automatic external fact or Shaelvien canon",
            "identityRule": "identity-is-not-output-equivalence",
        }

    def _event(self, entity_id, event_type, data):
        now = _now_ms()
        item = {
            "pk": self._entity_pk(entity_id),
            "sk": f"EVENT#{now:013d}#{uuid.uuid4()}",
            "eventType": event_type,
            "entityId": entity_id,
            "actor": self.actor,
            "createdAt": now,
            "data": _ddb_safe(data),
        }
        self.table.put_item(Item=item)

    def remember(self, args):
        entity_id = str(args.get("entityId") or ("relic-" + str(uuid.uuid4()))).strip()
        if not entity_id or len(entity_id) > 200:
            raise ValueError("Invalid entityId")
        old = self._profile(entity_id)
        if old and args.get("truthDomain") != old.get("truthDomain"):
            raise ValueError("Existing identity truthDomain changes require relic_transition")
        now = _now_ms()
        revision = int(old.get("revision", 0)) + 1 if old else 1
        aliases = []
        for value in [args["label"], *(args.get("aliases") or [])]:
            value = str(value).strip()
            if value and value not in aliases:
                aliases.append(value)
        item = {
            "pk": self._entity_pk(entity_id),
            "sk": "PROFILE",
            "actor": self.actor,
            "entityId": entity_id,
            "label": str(args["label"]).strip(),
            "entityType": str(args["entityType"]).strip(),
            "aliases": aliases,
            "attributes": _ddb_safe(args.get("attributes") or {}),
            "truthDomain": args["truthDomain"],
            "provenance": _ddb_safe(args["provenance"]),
            "sourceRef": str(args.get("sourceRef") or "").strip(),
            "observation": str(args.get("observation") or "").strip(),
            "revision": revision,
            "createdAt": int(old.get("createdAt", now)) if old else now,
            "updatedAt": now,
            "canonStatus": "non-canonical-relic-memory",
        }
        if old:
            self.table.put_item(
                Item=item,
                ConditionExpression="revision = :expected",
                ExpressionAttributeValues={":expected": int(old.get("revision", 1))},
            )
            self._event(entity_id, "remember.update", {
                "fromRevision": int(old.get("revision", 1)),
                "toRevision": revision,
                "previous": _compact_profile(old),
                "provenance": args["provenance"],
            })
        else:
            self.table.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
            self._event(entity_id, "remember.create", {
                "revision": 1,
                "provenance": args["provenance"],
            })
        for alias in aliases:
            self._write_alias(entity_id, alias, item["label"])
        return {
            "entity": _compact_profile(item),
            "created": old is None,
            "worldTruthChanged": False,
            "canonPromoted": False,
        }

    def relate(self, args):
        source_id = str(args["sourceId"])
        target_id = str(args["targetId"])
        if source_id == target_id and str(args["relationType"]).casefold() in {"same-as", "identical-to"}:
            raise ValueError("Self-equivalence relationship is redundant")
        source = self._profile(source_id)
        target = self._profile(target_id)
        if not source or not target:
            raise ValueError("Both sourceId and targetId must already exist")
        relation_id = str(uuid.uuid4())
        now = _now_ms()
        relation = {
            "relationId": relation_id,
            "sourceId": source_id,
            "relationType": str(args["relationType"]).strip(),
            "targetId": target_id,
            "truthDomain": args["truthDomain"],
            "provenance": _ddb_safe(args["provenance"]),
            "sourceRef": str(args.get("sourceRef") or "").strip(),
            "qualifiers": _ddb_safe(args.get("qualifiers") or {}),
            "createdAt": now,
        }
        self.table.put_item(Item={
            "pk": self._entity_pk(source_id),
            "sk": f"REL#{now:013d}#{relation_id}",
            **relation,
        })
        self.table.put_item(Item={
            "pk": self._entity_pk(target_id),
            "sk": f"IN#{now:013d}#{relation_id}",
            **relation,
        })
        self._event(source_id, "relationship.create", relation)
        return {
            "relationship": _plain(relation),
            "identityMerged": False,
            "worldTruthChanged": False,
            "canonPromoted": False,
        }

    def instantiate(self, args):
        basis = [str(x) for x in (args.get("basisEntityIds") or [])]
        missing = [x for x in basis if not self.exists(x)]
        if missing:
            raise ValueError("Unknown basisEntityIds: " + ",".join(missing))
        if args["truthDomain"] == "FACT":
            unstable = []
            for entity_id in basis:
                p = self._profile(entity_id)
                if p and p.get("truthDomain") in {"HYPOTHESIS", "UNKNOWN"}:
                    unstable.append(entity_id)
            if unstable:
                raise ValueError("Cannot instantiate FACT from unresolved basis identities: " + ",".join(unstable))
        result = self.remember({
            "label": args["label"],
            "entityType": args["entityType"],
            "attributes": args.get("attributes") or {},
            "truthDomain": args["truthDomain"],
            "provenance": args["provenance"],
            "sourceRef": args.get("sourceRef") or "",
            "observation": "Instantiated: " + str(args["commitReason"]),
            "aliases": [],
        })
        new_id = result["entity"]["entityId"]
        for basis_id in basis:
            self.relate({
                "sourceId": new_id,
                "relationType": "derived-from",
                "targetId": basis_id,
                "truthDomain": args["truthDomain"],
                "provenance": args["provenance"],
                "sourceRef": args.get("sourceRef") or "",
                "qualifiers": {"commitReason": args["commitReason"]},
            })
        result["basisEntityIds"] = basis
        return result

    def transition(self, args):
        entity_id = str(args["entityId"])
        old = self._profile(entity_id)
        if not old:
            raise ValueError("Entity not found")
        expected = args.get("expectedRevision")
        old_revision = int(old.get("revision", 1))
        if expected is not None and int(expected) != old_revision:
            raise ValueError(f"Revision conflict: expected {expected}, current {old_revision}")
        if args["truthDomain"] == "FACT" and not str(args.get("sourceRef") or "").strip():
            raise ValueError("FACT requires sourceRef")
        now = _now_ms()
        new_item = dict(old)
        new_item["attributes"] = _ddb_safe(args.get("toState") or {})
        new_item["truthDomain"] = args["truthDomain"]
        new_item["provenance"] = _ddb_safe(args["provenance"])
        new_item["sourceRef"] = str(args.get("sourceRef") or "").strip()
        new_item["revision"] = old_revision + 1
        new_item["updatedAt"] = now
        self.table.put_item(
            Item=new_item,
            ConditionExpression="revision = :expected",
            ExpressionAttributeValues={":expected": old_revision},
        )
        self._event(entity_id, "state.transition", {
            "reason": args["reason"],
            "fromRevision": old_revision,
            "toRevision": old_revision + 1,
            "fromTruthDomain": old.get("truthDomain"),
            "toTruthDomain": args["truthDomain"],
            "fromState": _plain(old.get("attributes") or {}),
            "toState": args.get("toState") or {},
            "provenance": args["provenance"],
            "sourceRef": args.get("sourceRef") or "",
        })
        return {
            "entity": _compact_profile(new_item),
            "previousRevision": old_revision,
            "worldTruthChanged": False,
            "canonPromoted": False,
        }

    def trace(self, entity_id, depth=2):
        if not self.exists(entity_id):
            raise ValueError("Entity not found")
        depth = max(0, min(int(depth), 5))
        nodes = {}
        edges = []
        queue = [(entity_id, 0)]
        seen_edges = set()
        while queue and len(nodes) < 100:
            current, level = queue.pop(0)
            if current in nodes or level > depth:
                continue
            profile = self._profile(current)
            if not profile:
                continue
            nodes[current] = _compact_profile(profile)
            if level >= depth:
                continue
            for edge in self._relationships(current, 50):
                edge_id = edge.get("relationId")
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append({
                        k: edge.get(k) for k in (
                            "relationId", "sourceId", "relationType", "targetId",
                            "truthDomain", "provenance", "sourceRef", "qualifiers", "createdAt"
                        )
                    })
                target = edge.get("targetId")
                if target and target not in nodes:
                    queue.append((target, level + 1))
        return {
            "rootEntityId": entity_id,
            "nodes": nodes,
            "edges": edges,
            "truthBoundary": "trace reports stored provenance and relations; it does not independently prove external truth",
        }

    def validate_claim(self, claim):
        if not isinstance(claim, dict):
            raise ValueError("claim must be an object")
        truth_domain = claim.get("truthDomain")
        if truth_domain not in {"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"}:
            raise ValueError("Invalid truthDomain")
        issues = []
        subject_id = claim.get("subjectId")
        object_id = claim.get("objectId")
        if subject_id and not self.exists(subject_id):
            issues.append({"code": "unknown-subject", "entityId": subject_id})
        if object_id and not self.exists(object_id):
            issues.append({"code": "unknown-object", "entityId": object_id})
        if truth_domain == "FACT" and not str(claim.get("sourceRef") or "").strip():
            issues.append({"code": "fact-without-source", "message": "FACT requires sourceRef"})
        return {
            "validStructure": not issues,
            "issues": issues,
            "truthDomain": truth_domain,
            "externalTruthVerified": False,
            "canonPromoted": False,
            "identityRule": "text-or-output-equivalence-does-not-prove-identity",
        }
