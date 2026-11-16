// Synthetic API fixtures are confined to browser tests. No provider or commercial data.
const p=require(process.env.FUEL_BROWSER_MODULE||'puppeteer');
const assert=require('node:assert/strict');
const base=process.env.BASE_URL||'http://127.0.0.1:8134';
(async()=>{
 const b=await p.launch({headless:true,args:['--no-sandbox','--ignore-certificate-errors','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']});
 const page=await b.newPage();let mode='error';let checks=0;const failures=[];
 const check=async fn=>{try{await fn()}catch(e){failures.push(e.message)}};
 await page.setRequestInterception(true);
 page.on('request',req=>{
  if(!req.url().includes('/api/v1/routes/optimize/'))return req.continue();
  const body=mode==='error'?{error:{code:'unknown_city',message:'City not found in the local catalog',details:{}}}:{route:{distance_miles:100,duration_minutes:120,geometry:{type:'LineString',coordinates:[[-87,41],[-86,41]]}},fuel:{purchased_en_route_usd:0,estimated_total_trip_cost_usd:30,initial_fuel_estimated_cost_usd:30},stops:[],meta:{routing_api_calls:1,cache_hit:false,warnings:['Station locations are approximate city centers, not verified fuel pump locations.']}};
  req.respond({status:mode==='error'?422:200,contentType:'application/json',body:JSON.stringify(body)});
 });
 try{
 await page.goto(base+'/demo/',{waitUntil:'networkidle2'});await page.waitForSelector('#map canvas');
 await page.select('#languageSelect','es');await page.click('#submitButton');await page.waitForSelector('#status.error');
 await check(async()=>assert.match(await page.$eval('#statusText',e=>e.textContent),/ciudad/i,'API unknown-city error must be localized in Spanish'));checks++;
 await page.select('#languageSelect','fr');
 await check(async()=>assert.equal(await page.$eval('#status',e=>e.classList.contains('error')),true,'language switch must preserve error state'));checks++;
 await check(async()=>assert.match(await page.$eval('#statusText',e=>e.textContent),/ville/i));checks++;
 mode='success';await page.select('#languageSelect','es');await page.click('#submitButton');await page.waitForSelector('#status.success');
 await check(async()=>assert.equal(await page.$eval('#warnings',e=>e.textContent.includes('Station locations')),false,'provider warning must not leak English into Spanish UI'));checks++;
 await page.$eval('#startCity',e=>{e.value='Boston';e.dispatchEvent(new Event('input',{bubbles:true}))});
 await check(async()=>assert.equal(await page.$eval('#metrics',e=>e.hidden),true,'editing a city must invalidate old results and copied summary'));checks++;
 await page.$eval('#startState',e=>{e.value='ZZ';e.dispatchEvent(new Event('input',{bubbles:true}))});
 await check(async()=>assert.equal(await page.$eval('#startState',e=>e.checkValidity()),false,'unknown state codes must fail client validation'));checks++;
 console.log(JSON.stringify({checks,result:failures.length?'failed':'passed',failures,fixtures:'synthetic; no live routing'},null,2));if(failures.length)process.exitCode=1;
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
