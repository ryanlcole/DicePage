(()=>{'use strict';

const inputs=[...document.querySelectorAll('[data-count]')];
const accounts=document.querySelector('[data-total-accounts]');
const mrr=document.querySelector('[data-mrr]');
const arr=document.querySelector('[data-arr]');
const money=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0});

function nonnegativeInt(value){
  const n=Number(value);
  return Number.isFinite(n)?Math.max(0,Math.floor(n)):0;
}

function recalc(){
  let count=0,total=0;
  for(const input of inputs){
    const n=nonnegativeInt(input.value);
    count+=n;
    total+=n*Number(input.dataset.price||0);
  }
  accounts.textContent=count.toLocaleString('en-US');
  mrr.textContent=money.format(total);
  arr.textContent=money.format(total*12);
}

function text(selector,value){
  const node=document.querySelector(selector);
  if(node)node.textContent=value;
}

function published(value,formatter){
  return value===null||value===undefined||value===''?'Not published':formatter?formatter(value):String(value);
}

async function loadCampaignRecord(){
  try{
    const response=await fetch('/kickstarter/campaign.json',{cache:'no-store'});
    if(!response.ok)throw new Error('Campaign record '+response.status);
    const data=await response.json();

    const status=String(data.campaignStatus||'unverified').replaceAll('-',' ');
    text('[data-campaign-record-status]',status);
    text('[data-campaign-goal]',published(data.fundingGoalUsd,v=>money.format(Number(v))));
    text('[data-campaign-launch]',published(data.launchDate));
    text('[data-campaign-rewards]',Array.isArray(data.rewardTiers)&&data.rewardTiers.length?String(data.rewardTiers.length):'Not published');
    text('[data-campaign-backers]',published(data.publishedBackerCount,v=>Number(v).toLocaleString('en-US')));
    text('[data-campaign-pledged]',published(data.publishedPledgedUsd,v=>money.format(Number(v))));
    text('[data-campaign-verified]',data.verifiedAt?'Repository record verified '+data.verifiedAt+'.':'Repository verification date not recorded.');

    const statusText=document.querySelector('[data-campaign-status]');
    if(statusText){
      statusText.textContent=data.publicCampaignUrl
        ? 'A public Kickstarter campaign URL is recorded in the project repository.'
        : 'Kickstarter account setup is in progress. No public campaign URL, funding goal, launch date, or reward tiers are recorded as published facts.';
    }

    const link=document.querySelector('[data-campaign-public-link]');
    if(link&&data.publicCampaignUrl){
      const url=new URL(String(data.publicCampaignUrl));
      if(url.protocol==='https:'&&/^(www\\.)?kickstarter\\.com$/i.test(url.hostname)){
        link.href=url.href;
        link.hidden=false;
      }
    }
  }catch(error){
    console.error('Kickstarter campaign record failed to load',error);
    text('[data-campaign-record-status]','Record unavailable');
    text('[data-campaign-goal]','Unknown');
    text('[data-campaign-launch]','Unknown');
    text('[data-campaign-rewards]','Unknown');
    text('[data-campaign-backers]','Unknown');
    text('[data-campaign-pledged]','Unknown');
    text('[data-campaign-verified]','Repository campaign record could not be loaded.');
  }
}

inputs.forEach(input=>input.addEventListener('input',recalc));
recalc();
loadCampaignRecord();
})();
