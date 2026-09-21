(() => {
  'use strict';
  const form=document.querySelector('[data-quote-form]');
  const message=document.querySelector('[data-form-message]');
  const empty=document.querySelector('[data-payment-empty]');
  const ready=document.querySelector('[data-payment-ready]');
  const total=document.querySelector('[data-total]');
  const accountOut=document.querySelector('[data-account]');
  const referenceOut=document.querySelector('[data-reference]');
  const costReferenceOut=document.querySelector('[data-cost-reference]');
  const methodOut=document.querySelector('[data-method]');
  const memo=document.querySelector('[data-memo]');
  const paypalPanel=document.querySelector('[data-paypal-panel]');
  const bitcoinPanel=document.querySelector('[data-bitcoin-panel]');
  const paypalLink=document.querySelector('[data-paypal-link]');
  const btcAddress=document.querySelector('[data-btc-address]');
  const transactionId=document.querySelector('[data-transaction-id]');
  const claim=document.querySelector('[data-claim]');
  const copyMemo=document.querySelector('[data-copy-memo]');
  const copyBtc=document.querySelector('[data-copy-btc]');
  const copyClaim=document.querySelector('[data-copy-claim]');
  let policy=null;
  let prepared=null;
  const clean=(value,max=160)=>String(value??'').trim().replace(/[\r\n|]+/g,' ').slice(0,max);
  const money=cents=>new Intl.NumberFormat(undefined,{style:'currency',currency:'USD'}).format(cents/100);
  function makeReference(){const bytes=new Uint8Array(5);crypto.getRandomValues(bytes);const random=[...bytes].map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase();return 'RAI-'+Date.now().toString(36).toUpperCase()+'-'+random}
  function validAccount(value){return /^[A-Za-z0-9._:@-]{3,160}$/.test(value)}
  function toCents(value){const text=String(value??'').trim();if(!/^\d+(?:\.\d{1,2})?$/.test(text))return null;const amount=Number(text);if(!Number.isFinite(amount)||amount<=0||amount>1000000)return null;return Math.round(amount*100)}
  async function copyText(value,button){if(!value)return;try{await navigator.clipboard.writeText(value);const old=button.textContent;button.textContent='Copied';setTimeout(()=>{button.textContent=old},1200)}catch{message.textContent='Copy was blocked by the browser. Select the text and copy it manually.'}}
  function buildClaim(){if(!prepared)return '';return JSON.stringify({schema:'relic-ai-payment-claim-v0',accountId:prepared.accountId,purchaseReference:prepared.reference,costReference:prepared.costReference,service:prepared.service,verifiedServiceCostUsdCents:prepared.costCents,markupPercent:policy.pricing.markupPercent,amountDueUsdCents:prepared.totalCents,paymentMethod:prepared.method,paymentTransactionReference:clean(transactionId.value,180),status:'submitted-for-manual-verification',automaticEntitlement:false,createdAtUtc:new Date().toISOString()},null,2)}
  function refreshClaim(){claim.value=buildClaim()}
  async function loadPolicy(){try{const response=await fetch('/ai-purchase/commerce.json',{cache:'no-store'});if(!response.ok)throw new Error('commerce manifest '+response.status);const loaded=await response.json();if(loaded?.pricing?.multiplier!==1.8||loaded?.fulfillment?.automaticEntitlement!==false||loaded?.population?.minimumHumansPerExternalAi!==10)throw new Error('commerce manifest failed required policy checks');policy=loaded;paypalLink.href=policy.paymentMethods.paypal.url;btcAddress.textContent=policy.paymentMethods.bitcoin.address}catch(error){console.error('ReLiC agent-commerce policy unavailable',error);message.textContent='Commerce policy could not be verified. Payment preparation is disabled.';form.querySelector('button[type="submit"]').disabled=true}}
  form.addEventListener('submit',event=>{event.preventDefault();message.textContent='';if(!policy){message.textContent='Commerce policy is not available.';return}const data=new FormData(form);const accountId=clean(data.get('accountId'));const costReference=clean(data.get('costReference'),80);const service=clean(data.get('service'),80);const costCents=toCents(data.get('serviceCost'));const method=clean(data.get('paymentMethod'),20);if(!validAccount(accountId)){message.textContent='Enter a valid Shaelvien/ReLiC account ID.';return}if(!costReference||!service||costCents===null){message.textContent='Account, ReLiC cost reference, service, and verified service cost are required.';return}if(!['paypal','bitcoin'].includes(method)){message.textContent='Select a supported payment method.';return}const totalCents=Math.round(costCents*policy.pricing.multiplier);const reference=makeReference();const methodName=method==='bitcoin'?'Bitcoin / native BTC':'PayPal';const note=['RELIC-AI','acct='+accountId,'purchase='+reference,'costRef='+costReference,'service='+service,'dueUSD='+(totalCents/100).toFixed(2),'method='+method].join(' | ');prepared={accountId,costReference,service,costCents,totalCents,reference,method,note};total.textContent=money(totalCents);accountOut.textContent=accountId;referenceOut.textContent=reference;costReferenceOut.textContent=costReference;methodOut.textContent=methodName;memo.value=note;paypalPanel.hidden=method!=='paypal';bitcoinPanel.hidden=method!=='bitcoin';empty.hidden=true;ready.hidden=false;transactionId.value='';refreshClaim();ready.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'})});
  transactionId.addEventListener('input',refreshClaim);
  copyMemo.addEventListener('click',()=>copyText(memo.value,copyMemo));
  copyBtc.addEventListener('click',()=>copyText(btcAddress.textContent,copyBtc));
  copyClaim.addEventListener('click',()=>{refreshClaim();copyText(claim.value,copyClaim)});
  loadPolicy();
})();
