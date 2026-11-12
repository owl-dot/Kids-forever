const {chromium}=require('playwright');
(async()=>{
 const [,,mode,a,b]=process.argv;
 const br=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const pg=await br.newPage({viewport:{width:1080,height:1920}});
 pg.on('console',m=>console.log('C:',m.text()));pg.on('pageerror',e=>console.log('ERR:',e.message));
 await pg.goto('http://127.0.0.1:8765/index.html');
 await pg.waitForFunction(()=>window.ready===true,{timeout:60000});
 const times = mode==='prev' ? a.split(',').map(Number) : null;
 if(times){for(const t of times){await pg.evaluate(t=>renderAt(t),t);await pg.screenshot({path:`prev_${t}.jpg`,type:'jpeg',quality:85});}}
 else{const f0=+a,f1=+b;for(let f=f0;f<f1;f++){await pg.evaluate(t=>renderAt(t),f/30);await pg.screenshot({path:`frames/f${String(f).padStart(4,'0')}.jpg`,type:'jpeg',quality:93});}}
 await br.close();
})();
