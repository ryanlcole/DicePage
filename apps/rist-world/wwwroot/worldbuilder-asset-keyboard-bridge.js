(()=>{
 'use strict';

 function ensureKeyboardInputAuthority(){
  if(window.RistWorldBuilderKeyboardInput)return;
  if(document.querySelector('script[data-rist-worldbuilder-keyboard-input="1"]'))return;
  const script=document.createElement('script');
  script.src='./worldbuilder-keyboard-input-authority.js?v=20260917-keyboard-input-1';
  script.async=false;
  script.dataset.ristWorldbuilderKeyboardInput='1';
  (document.head||document.documentElement).appendChild(script);
 }

 ensureKeyboardInputAuthority();

 const api={
  attach(dotnet){
   window.RistWorldBuilderStudioDotNet=dotnet;
   ensureKeyboardInputAuthority();
   try{window.dispatchEvent(new CustomEvent('rist:worldbuilder-dotnet-ready',{detail:{dotnet}}))}catch{}
  },
  detach(dotnet){if(window.RistWorldBuilderStudioDotNet===dotnet)window.RistWorldBuilderStudioDotNet=null}
 };
 window.RistWorldBuilderAssetKeyboardBridge=api;
})();
