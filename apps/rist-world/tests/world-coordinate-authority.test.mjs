import assert from 'node:assert/strict';

globalThis.window={ristWorld:{}};
await import(new URL('../wwwroot/world-coordinate-authority.js',import.meta.url));
const A=window.ristWorldCoordinates;
assert.ok(A,'coordinate authority exported');

const rect={left:100,top:50,width:600,height:600};
const center=A.worldPointFromClient(rect,400,350,0,0,1);
assert.deepEqual(center,[0.5,0.5]);

const snapped=A.snapWorldPoint(0,0,30,30);
assert.equal(snapped[0],1/60);
assert.equal(snapped[1],1/60);

const far=A.snapWorldPoint(.999999,.999999,30,30);
assert.equal(far[0],59/60);
assert.equal(far[1],59/60);

const el={getBoundingClientRect:()=>rect};
const noTransform=A.tileDropPoint(el,400,350,0,0,1,30,30);
assert.deepEqual(noTransform,[1,31/60,31/60]);

// Pointer is transformed into world coordinates before snapping. With 2x zoom,
// a screen point at 75% width is world x=.625 and therefore snaps to cell 18.
const zoomed=A.tileDropPoint(el,550,350,0,0,2,30,30);
assert.equal(zoomed[0],1);
assert.equal(zoomed[1],37/60);
assert.equal(zoomed[2],31/60);

// Pan also participates before snapping; screen-space snapping would fail here.
const panned=A.tileDropPoint(el,400,350,60,0,1,30,30);
assert.equal(panned[1],25/60);
assert.equal(panned[2],31/60);

assert.deepEqual(A.tileDropPoint(el,50,50,0,0,1,30,30),[0,0,0]);
console.log('world-coordinate-authority: ok');
