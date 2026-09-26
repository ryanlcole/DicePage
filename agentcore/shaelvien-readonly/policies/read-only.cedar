// Replace <gateway-arn> after the gateway is deployed.
//
// AgentCore Policy uses default-deny semantics in ENFORCE mode.
// This policy permits only the three explicitly read-only tools.
// There is deliberately no wildcard permit.

permit(
  principal,
  action in [
    AgentCore::Action::"RistReadOnlyKnowledge___health",
    AgentCore::Action::"RistReadOnlyKnowledge___get_record",
    AgentCore::Action::"RistReadOnlyKnowledge___query_scope"
  ],
  resource == AgentCore::Gateway::"<gateway-arn>"
);
