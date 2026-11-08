/* Universal Roll20 Sheet v0.1 — script copied into <script type="text/worker">.
   Only Roll20 sheet worker APIs. Never touches the DOM or runs user macros. */
(function () {
  'use strict';

  function numberOr(value, fallback) {
    if (value === '' || value === null || typeof value === 'undefined') return fallback;
    var n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }
  function validNumber(value, fallback, min, max) {
    var n = numberOr(value, fallback);
    return Number.isInteger(n) && n >= min && n <= max ? n : null;
  }
  function safeLabel(value) {
    var label = String(value || 'Dice roll').replace(/[\r\n{}[\]<>|]/g, ' ').replace(/\s+/g, ' ').trim();
    return (label || 'Dice roll').slice(0, 80);
  }
  function computeRecipe(v) {
    if (v.recipe_mode === 'manual') {
      var raw = String(v.recipe_manual || '').trim();
      // Roll20 roll buttons expect one chat command per entry. Reject accidental multiline macros.
      if (!raw || raw.length > 650 || /[\r\n]/.test(raw)) {
        return {command: '/em Dice recipe needs a single valid command', status: 'Fix manual command'};
      }
      if (!/^(\/roll\s|\/r\s|\/w\s|\/em\s|&\{template:|!\S|%\{|#[A-Za-z0-9_-]+)/i.test(raw)) {
        return {command: '/em Dice recipe needs a Roll20 command', status: 'Use /roll, /r, /w, /em, a template, %Ability, #macro or !Mod'};
      }
      return {command: raw, status: 'Manual command ready'};
    }
    var qty = validNumber(v.recipe_count, 1, 1, 100);
    var sidesChoice = String(v.recipe_sides || '20');
    var sides = sidesChoice === 'custom' ? validNumber(v.recipe_customsides, 6, 2, 1000) :
       (sidesChoice === 'F' ? 'F' : validNumber(sidesChoice, 20, 2, 1000));
    if (qty === null || sides === null) return {command:'/em Invalid dice',status:'Check number of dice and sides'};
    var keep = String(v.recipe_keep || 'none');
    if (!/^(none|kh|kl|dh|dl)$/.test(keep)) keep = 'none';
    var keepCount = validNumber(v.recipe_keepcount, 1, 1, qty);
    if (keep !== 'none' && (qty < 2 || keepCount === null || (keep[0] === 'd' && keepCount >= qty))) {
      return {command:'/em Invalid keep/drop',status:'Check keep/drop count'};
    }
    var reroll = String(v.recipe_reroll || 'none');
    if (!/^(none|r1|ro1)$/.test(reroll)) reroll = 'none';
    var bonus = validNumber(v.recipe_bonus, 0, -100000, 100000);
    if (bonus === null) return {command:'/em Invalid bonus',status:'Bonus must be an integer'};
    var targetInput = v.recipe_target;
    var hasTarget = !(targetInput === '' || targetInput === null || typeof targetInput === 'undefined');
    var target = hasTarget ? validNumber(targetInput, 1, 0, 1000) : null;
    if (hasTarget && target === null) return {command:'/em Invalid target',status:'Target must be a nonnegative integer'};
    if (sides === 'F' && (reroll !== 'none' || v.recipe_explode === '1' || hasTarget)) {
      return {command:'/em Unsupported Fate modifiers',status:'Use Manual mode for advanced Fate rolls'};
    }
    var expr = qty + 'd' + sides;
    if (v.recipe_explode === '1') expr += '!';
    if (reroll !== 'none') expr += reroll;
    if (keep !== 'none') expr += keep + keepCount;
    if (hasTarget) expr += '>' + target;
    if (bonus > 0) expr += '+' + bonus;
    if (bonus < 0) expr += String(bonus);
    var label = safeLabel(v.recipe_name);
    var prefix = v.recipe_visibility === 'gm' ? '/w gm ' : '';
    return {command: prefix + '&{template:default} {{name=' + label + '}} {{Roll=[[' + expr + ']]}}', status:'Ready: ' + expr};
  }

  function refreshRecipe(event) {
    var source = event && event.sourceAttribute || '';
    var match = /^repeating_dicebag_([^_]+)_/.exec(source);
    if (!match) return;
    var pre = 'repeating_dicebag_' + match[1] + '_';
    var fields = ['recipe_name','recipe_mode','recipe_count','recipe_sides','recipe_customsides','recipe_keep','recipe_keepcount','recipe_bonus','recipe_reroll','recipe_explode','recipe_target','recipe_visibility','recipe_manual'];
    getAttrs(fields.map(function (f) {return pre + f;}), function (raw) {
      var v = {};
      fields.forEach(function (f) {v[f] = raw[pre+f];});
      var result = computeRecipe(v);
      var update = {};
      update[pre+'recipe_command'] = result.command;
      update[pre+'recipe_status'] = result.status;
      setAttrs(update, {silent: true});
    });
  }

  on('change:repeating_dicebag:recipe_name change:repeating_dicebag:recipe_mode change:repeating_dicebag:recipe_count change:repeating_dicebag:recipe_sides change:repeating_dicebag:recipe_customsides change:repeating_dicebag:recipe_keep change:repeating_dicebag:recipe_keepcount change:repeating_dicebag:recipe_bonus change:repeating_dicebag:recipe_reroll change:repeating_dicebag:recipe_explode change:repeating_dicebag:recipe_target change:repeating_dicebag:recipe_visibility change:repeating_dicebag:recipe_manual', refreshRecipe);

  function sumRepeating(section, fieldNames, calculator, output) {
    getSectionIDs('repeating_' + section, function (ids) {
      var attrs = [];
      ids.forEach(function (id) { fieldNames.forEach(function (f) {attrs.push('repeating_'+section+'_'+id+'_'+f);}); });
      if (!attrs.length) { var empty = {}; empty[output] = 0; setAttrs(empty, {silent:true}); return; }
      getAttrs(attrs, function (v) {
        var total = 0;
        ids.forEach(function (id) {
          var obj = {};
          fieldNames.forEach(function (f) {obj[f] = v['repeating_'+section+'_'+id+'_'+f];});
          total += calculator(obj);
        });
        var update = {}; update[output] = Math.round(total*100)/100;
        setAttrs(update, {silent:true});
      });
    });
  }
  function sumGear() {
    sumRepeating('gear', ['gear_carried','gear_qty','gear_weight'], function (v) {
      if (v.gear_carried !== '1') return 0;
      var qty = numberOr(v.gear_qty, 0), weight = numberOr(v.gear_weight, 0);
      return Number.isFinite(qty * weight) && qty >= 0 && weight >= 0 ? qty*weight : 0;
    }, 'carried_weight');
  }
  function sumPrepared() {
    sumRepeating('spells', ['spell_prepared'], function (v) {
      var count = numberOr(v.spell_prepared, 0);
      return Number.isInteger(count) && count > 0 ? count : 0;
    }, 'prepared_total');
  }
  on('change:repeating_gear:gear_carried change:repeating_gear:gear_qty change:repeating_gear:gear_weight remove:repeating_gear', sumGear);
  on('change:repeating_spells:spell_prepared remove:repeating_spells', sumPrepared);
  on('sheet:opened', function () {sumGear(); sumPrepared();});
})();
