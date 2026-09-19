(()=>{'use strict';
const inputs=[...document.querySelectorAll('[data-count]')];
const accounts=document.querySelector('[data-total-accounts]');
const mrr=document.querySelector('[data-mrr]');
const arr=document.querySelector('[data-arr]');
const money=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0});
function nonnegativeInt(value){const n=Number(value);return Number.isFinite(n)?Math.max(0,Math.floor(n)):0}
function recalc(){let count=0,total=0;for(const input of inputs){const n=nonnegativeInt(input.value);count+=n;total+=n*Number(input.dataset.price||0)}accounts.textContent=count.toLocaleString('en-US');mrr.textContent=money.format(total);arr.textContent=money.format(total*12)}
inputs.forEach(input=>input.addEventListener('input',recalc));recalc();
})();