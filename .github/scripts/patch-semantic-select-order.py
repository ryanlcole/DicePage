from pathlib import Path

path = Path('apps/rist-world/Components/UniversalInterface.SemanticControls.cs')
text = path.read_text(encoding='utf-8')
old = '''        if (_stage == Stage.SpatialSelect && _regionDefinerOpen)
        {
            _builderChainIndex = 1;
            _requestedBuilderChainIndex = 1;
            _assetScope = "REGION";
            await SelectRegionDefinerAsync();
            return;
        }

        if ((_stage == Stage.BrowsePlace || _stage == Stage.MmoMap) && CursorMode)
        {
            await ActivateBrowseCursorTargetAsync();
            return;
        }
'''
new = '''        if ((_stage == Stage.BrowsePlace || _stage == Stage.MmoMap) && CursorMode)
        {
            await ActivateBrowseCursorTargetAsync();
            return;
        }

        if (_stage == Stage.SpatialSelect && _regionDefinerOpen)
        {
            _builderChainIndex = 1;
            _requestedBuilderChainIndex = 1;
            _assetScope = "REGION";
            await SelectRegionDefinerAsync();
            return;
        }
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f'Expected SelectSemantic routing block exactly once; found {count}')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
