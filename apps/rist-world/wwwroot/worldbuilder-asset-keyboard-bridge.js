(()=>{
 'use strict';
 const api={
  attach(dotnet){
   window.RistWorldBuilderStudioDotNet=dotnet;
   try{window.dispatchEvent(new CustomEvent('rist:worldbuilder-dotnet-ready',{detail:{dotnet}}))}catch{}
  },
  detach(dotnet){if(window.RistWorldBuilderStudioDotNet===dotnet)window.RistWorldBuilderStudioDotNet=null}
 };
 window.RistWorldBuilderAssetKeyboardBridge=api;
})();
