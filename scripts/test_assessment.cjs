/* Reproducible real-browser assessment: both pages, seven viewports, four locales,
 * dark/light themes, persistence and arithmetic-only landing controls.
 * No synthetic provider response is used in these visual captures. */
const p=require(process.env.FUEL_BROWSER_MODULE||'puppeteer');
const assert=require('node:assert/strict');const fs=require('node:fs');
const base=process.env.BASE_URL||'http://127.0.0.1:8134';
const out='docs/assessment-2026-11-16';const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const b=await p.launch({headless:true,args:['--no-sandbox','--ignore-certificate-errors','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']});
 const page=await b.newPage();const errors=[];const states=[];let checks=0;
 page.on('pageerror',e=>errors.push(e.message));const check=(value,msg)=>{assert.ok(value,msg);checks++};
 fs.mkdirSync(out+'/after',{recursive:true});
 try{
  await page.evaluateOnNewDocument(()=>{Object.defineProperty(navigator,'language',{get:()=> 'fr-FR'})});
  await page.goto(base,{waitUntil:'networkidle2'});
  check(await page.evaluate(()=>document.documentElement.lang==='en'&&document.documentElement.dataset.theme==='dark'),'fresh browser defaults to English and dark regardless of system locale');
  const sizes=[[320,720],[375,812],[430,932],[768,1024],[1280,800],[1440,900],[1920,1080]];
  for(const [width,height]of sizes){
   for(const [name,path,select]of [['landing','/','#language'],['planner','/demo/','#languageSelect']]){
    await page.setViewport({width,height});await page.goto(base+path,{waitUntil:'networkidle2'});
    if(name==='planner')await page.waitForSelector('#map canvas');
    for(const theme of ['dark','light']){
     if(await page.evaluate(()=>document.documentElement.dataset.theme)!==theme)await page.click('#themeToggle');
     for(const lang of ['en','es','fr','pt']){
      await page.select(select,lang);
      const data=await page.evaluate(()=>{
       const root=document.documentElement;
       const badButtons=[...document.querySelectorAll('button')].filter(el=>el.offsetWidth&&el.scrollWidth>el.clientWidth+2).map(e=>e.id||e.textContent.trim());
       return {lang:root.lang,theme:root.dataset.theme,overflow:root.scrollWidth>innerWidth,heading:document.querySelector('h1').textContent,buttonClipping:badButtons,
        lightHidden:document.querySelector('[data-theme-light-icon]').hasAttribute('hidden'),darkHidden:document.querySelector('[data-theme-dark-icon]').hasAttribute('hidden'),
        themeAria:document.querySelector('#themeToggle').getAttribute('aria-label')};
      });
      check(data.lang.startsWith(lang)&&data.theme===theme,`${width} ${name} ${theme} ${lang}: selected state`);
      check(!data.overflow,`${width} ${name} ${lang}: no horizontal overflow`);
      check(data.buttonClipping.length===0,`${width} ${name} ${lang}: button clipping ${data.buttonClipping}`);
      check(data.lightHidden===(theme==='light')&&data.darkHidden===(theme==='dark'),'theme icons reflect target mode');
      check(lang==='en'||!data.themeAria.startsWith('Switch'),'theme accessible label localized');
      states.push({width,height,page:name,theme,language:lang,heading:data.heading});
     }
     await page.select(select,'en');
     if(name==='landing'){
      await page.click('[data-distance="750"]');
      check(await page.$eval('#gallonsValue',e=>e.textContent)==='75','750 mi / 10 MPG = 75 gal');
      check(await page.$eval('#refillValue',e=>e.textContent)==='1','750 mi needs at least one refill from full tank');
      check(await page.$eval('#gallonsValue',e=>parseFloat(getComputedStyle(e).fontSize))>=28,'gallons figure has numeric hierarchy');
      await page.$eval('#distanceSlider',e=>{e.value='500';e.dispatchEvent(new Event('input',{bubbles:true}))});
      check(await page.$eval('#refillValue',e=>e.textContent)==='0','500 mi boundary requires no refill');
      await page.$eval('#distanceSlider',e=>{e.value='1050';e.dispatchEvent(new Event('input',{bubbles:true}))});
     }
     // Capture a true full-height viewport to keep the WebGL canvas rendered.
     const fullHeight=await page.evaluate(()=>document.documentElement.scrollHeight);
     await page.setViewport({width,height:fullHeight});await page.evaluate(()=>window.scrollTo(0,0));await pause(name==='planner'?1800:100);
     await page.screenshot({path:`${out}/after/${name}-${width}-${theme}.png`});
     await page.setViewport({width,height});
    }
   }
  }
  await page.goto(base,{waitUntil:'networkidle2'});await page.select('#language','pt');
  if(await page.evaluate(()=>document.documentElement.dataset.theme)!=='light')await page.click('#themeToggle');
  await page.goto(base+'/demo/',{waitUntil:'networkidle2'});await page.waitForSelector('#map canvas');
  check(await page.$eval('#languageSelect',e=>e.value)==='pt','language shared between pages');
  check(await page.evaluate(()=>document.documentElement.dataset.theme)==='light','theme shared between pages');
  await page.reload({waitUntil:'networkidle2'});
  check(await page.$eval('#languageSelect',e=>e.value)==='pt','language survives reload');
  check(await page.evaluate(()=>document.documentElement.dataset.theme)==='light','theme survives reload');
  await page.click('#swapButton');check(await page.$eval('#startCity',e=>e.value)==='Denver','swap route');
  await page.click('.preset');check(await page.$eval('#startCity',e=>e.value)==='Chicago','preset route');
  for(const id of ['startCity','finishCity']){
   await page.focus('#'+id);await page.$eval('#'+id,e=>{e.value='Chic';e.dispatchEvent(new Event('input',{bubbles:true}))});
   const menu=id==='startCity'?'startCityOptions':'finishCityOptions';await page.waitForSelector('#'+menu+' [role="option"]');
   await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
   check(await page.$eval('#'+id,e=>e.getAttribute('aria-expanded'))==='false',id+' keyboard selection');
  }
  for(const style of ['positron','dark','liberty']){
   await page.click(`[data-map-style="${style}"]`);check(await page.$eval(`[data-map-style="${style}"]`,e=>e.getAttribute('aria-pressed'))==='true','map style toggle');
  }
  check(errors.length===0,'no browser exceptions: '+errors.join(';'));
  const report={result:'passed',checks,visualStates:states.length,viewports:sizes,locales:['en','es','fr','pt'],themes:['dark','light'],browser:await b.version(),errors,states,provider:'Not exercised; no ORS key. Real city catalog and real map assets.'};
  fs.writeFileSync(out+'/browser-results.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({checks,visualStates:states.length,result:'passed',errors},null,2));
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
