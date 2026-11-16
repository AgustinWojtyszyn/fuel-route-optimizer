/* Landing-only narrative and illustration. It never calls the routing API. */
(() => {
  const translations = {
    en:{
      navMethod:"The method",navPlanner:"Route planner",headline:"Distance tells half the story.",
      intro:"The other half is fuel. Explore US road routes, estimate where refueling may be needed and understand the cost assumptions before you drive.",
      cta:"Open the route planner",secondary:"Explore the method",heroFoot:"Django API · HeiGIT routing · OpenFreeMap",
      instrumentTitle:"The range assumption",instrumentSub:"Five equal 100-mile sections",
      instrumentUnit:"mi",instrumentCaption:"An assumed full tank covers up to 500 miles at 10 mpg.",
      instrumentBottom:"50 gallons in the starting tank, assumed full.",instrumentFormula:"50 gal × 10 mpg",
      methodHeading:"The road. The prices. The decision.",
      methodIntro:"Real route geometry meets the supplied fuel-price dataset. The result separates money spent on new fuel from the estimated value already in the starting tank.",
      method1Title:"Follow the road",method1Text:"HeiGIT provides road distance and geometry for the route you request. This is not a straight-line mileage estimate.",
      method2Title:"Consider fuel prices",method2Text:"The supplied dataset contains undated fuel-price observations. Station locations are approximate city coordinates.",
      method3Title:"Show the trade-off",method3Text:"The optimizer proposes fuel purchases and reports their cost, alongside the assumptions and limitations.",
      labHeading:"What does 500 miles really mean?",labIntro:"Change a hypothetical trip distance to see how the assumed range affects fuel consumption and the minimum number of refills.",
      labWarning:"Illustration only. These are arithmetic limits, not a road route, verified stations or optimized purchases.",
      distanceLabel:"Hypothetical distance",stopsLabel:"Minimum refills",gallonsLabel:"Fuel consumed",distanceUnit:"miles",gallonsUnit:"gallons",
      closeHeading:"Ready to test a real route?",closeText:"Choose two US cities to see the actual road geometry, estimated fuel stops and fuel costs.",closeCta:"Start planning",
      disclaimer:"Fuel prices are undated observations. Suggested station markers use approximate city positions, not verified pump entrances.",
      footerLink:"Source code",pageTitle:"Fuel Route Optimizer | Fuel-aware US route planning"
    },
    es:{
      navMethod:"El método",navPlanner:"Planificador",headline:"La distancia cuenta solo la mitad.",
      intro:"La otra mitad es el combustible. Explorá rutas por Estados Unidos, estimá cuándo podrías necesitar cargar y entendé los supuestos antes de salir.",
      cta:"Abrir el planificador",secondary:"Conocer el método",heroFoot:"API Django · Rutas HeiGIT · OpenFreeMap",
      instrumentTitle:"La autonomía supuesta",instrumentSub:"Cinco tramos iguales de 100 millas",
      instrumentUnit:"mi",instrumentCaption:"Suponemos que un tanque lleno permite recorrer hasta 500 millas a 10 MPG.",
      instrumentBottom:"50 galones en el tanque inicial, supuesto lleno.",instrumentFormula:"50 gal × 10 mpg",
      methodHeading:"El camino. Los precios. La decisión.",
      methodIntro:"Las rutas reales se combinan con el archivo de precios. El resultado separa las compras nuevas del valor estimado del combustible inicial.",
      method1Title:"Seguir la carretera",method1Text:"HeiGIT proporciona distancias y geometría de las rutas solicitadas, no distancias en línea recta.",
      method2Title:"Evaluar los precios",method2Text:"El archivo contiene observaciones de precios sin fecha. Las estaciones tienen ubicaciones aproximadas por ciudad.",
      method3Title:"Mostrar las alternativas",method3Text:"El optimizador propone cargas de combustible e informa sus costos, supuestos y limitaciones.",
      labHeading:"¿Qué significan 500 millas?",labIntro:"Cambiá una distancia hipotética para entender cómo influye la autonomía sobre el consumo y las cargas mínimas.",
      labWarning:"Solo una ilustración aritmética. No representa un recorrido, estaciones verificadas ni compras optimizadas.",
      distanceLabel:"Distancia hipotética",stopsLabel:"Cargas mínimas",gallonsLabel:"Combustible consumido",distanceUnit:"millas",gallonsUnit:"galones",
      closeHeading:"¿Probamos una ruta real?",closeText:"Elegí dos ciudades de Estados Unidos para ver el recorrido, las paradas y los costos estimados.",closeCta:"Planificar ruta",
      disclaimer:"Los precios provienen de observaciones sin fecha. Los marcadores son ubicaciones aproximadas por ciudad, no surtidores verificados.",
      footerLink:"Código fuente",pageTitle:"Fuel Route Optimizer | Planificación de rutas en EE. UU."
    },
    fr:{
      navMethod:"La méthode",navPlanner:"Planificateur",headline:"La distance ne dit pas tout.",
      intro:"Le carburant compte aussi. Explorez des itinéraires aux États-Unis, estimez les besoins en ravitaillement et comprenez les hypothèses avant le départ.",
      cta:"Ouvrir le planificateur",secondary:"Découvrir la méthode",heroFoot:"API Django · Itinéraires HeiGIT · OpenFreeMap",
      instrumentTitle:"Hypothèse d'autonomie",instrumentSub:"Cinq segments égaux de 100 miles",
      instrumentUnit:"mi",instrumentCaption:"Un plein est supposé permettre jusqu'à 500 miles à 10 miles par gallon.",
      instrumentBottom:"50 gallons dans le réservoir de départ, supposé plein.",instrumentFormula:"50 gal × 10 mpg",
      methodHeading:"La route. Les prix. Le choix.",
      methodIntro:"Le tracé routier réel est associé au fichier des prix. Le résultat distingue les nouveaux achats de la valeur du carburant initial.",
      method1Title:"Suivre les routes",method1Text:"HeiGIT fournit la distance et la géométrie routières demandées, et non une distance à vol d'oiseau.",
      method2Title:"Examiner les prix",method2Text:"Le fichier contient des observations de prix non datées. Les stations sont situées approximativement par ville.",
      method3Title:"Éclairer la décision",method3Text:"L'optimiseur propose des achats et affiche leurs coûts, hypothèses et limites.",
      labHeading:"Que signifient 500 miles ?",labIntro:"Faites varier une distance hypothétique pour voir son effet sur la consommation et le minimum de ravitaillements.",
      labWarning:"Illustration arithmétique uniquement : ni itinéraire, ni stations vérifiées, ni achats optimisés.",
      distanceLabel:"Distance hypothétique",stopsLabel:"Pleins minimum",gallonsLabel:"Carburant consommé",distanceUnit:"miles",gallonsUnit:"gallons",
      closeHeading:"Tester un vrai trajet ?",closeText:"Choisissez deux villes américaines pour voir les routes, les arrêts et les coûts estimés.",closeCta:"Planifier",
      disclaimer:"Les prix proviennent d'observations non datées. Les marqueurs indiquent des villes approximatives, et non des pompes vérifiées.",
      footerLink:"Code source",pageTitle:"Fuel Route Optimizer | Itinéraires et carburant"
    },
    pt:{
      navMethod:"O método",navPlanner:"Planejador",headline:"A distância é só metade da história.",
      intro:"A outra metade é combustível. Explore rotas nos Estados Unidos, estime onde será preciso abastecer e entenda as premissas antes de viajar.",
      cta:"Abrir o planejador",secondary:"Conhecer o método",heroFoot:"API Django · Rotas HeiGIT · OpenFreeMap",
      instrumentTitle:"Autonomia considerada",instrumentSub:"Cinco partes iguais de 100 milhas",
      instrumentUnit:"mi",instrumentCaption:"Um tanque cheio é considerado suficiente para até 500 milhas a 10 mpg.",
      instrumentBottom:"50 galões no tanque inicial, considerado cheio.",instrumentFormula:"50 gal × 10 mpg",
      methodHeading:"A estrada. Os preços. A decisão.",
      methodIntro:"O traçado real da rota é combinado com o arquivo de preços. O resultado distingue novas compras do valor do combustível inicial.",
      method1Title:"Seguir a estrada",method1Text:"O HeiGIT fornece distância e geometria rodoviárias, não uma aproximação em linha reta.",
      method2Title:"Considerar os preços",method2Text:"O arquivo contém observações de preços sem data. Os postos têm posições aproximadas por cidade.",
      method3Title:"Explicar o resultado",method3Text:"O otimizador sugere compras de combustível e apresenta custos, premissas e limitações.",
      labHeading:"O que significam 500 milhas?",labIntro:"Altere uma distância hipotética para entender o consumo e a quantidade mínima de abastecimentos.",
      labWarning:"Somente uma ilustração matemática: não é uma rota, não verifica postos e não otimiza compras.",
      distanceLabel:"Distância hipotética",stopsLabel:"Paradas mínimas",gallonsLabel:"Combustível consumido",distanceUnit:"milhas",gallonsUnit:"galões",
      closeHeading:"Vamos testar uma rota real?",closeText:"Escolha duas cidades dos Estados Unidos para ver a rota, as paradas e os custos estimados.",closeCta:"Planejar",
      disclaimer:"Os preços são observações sem data. Os marcadores são locais aproximados por cidade, não bombas de combustível verificadas.",
      footerLink:"Código-fonte",pageTitle:"Fuel Route Optimizer | Planejamento de rotas nos EUA"
    }
  };
  const langSelect=document.getElementById('language');
  const slider=document.getElementById('distanceSlider');
  const rangeVisual=document.getElementById('rangeSegments');
  const supported=Object.keys(translations);
  let language='en';
  try{
    const previous=localStorage.getItem('fuel-route-language-v2');
    if(supported.includes(previous))language=previous;
  }catch(_){}
  const formatNumber=(value)=>new Intl.NumberFormat(
    {en:'en-US',es:'es-AR',fr:'fr-FR',pt:'pt-BR'}[language],
    {maximumFractionDigits:1}
  ).format(value);
  function updateRange(){
    if(!slider||!rangeVisual)return;
    const distance=Number(slider.value);
    const refills=Math.max(0,Math.ceil(distance/500)-1);
    const usedGallons=distance/10;
    document.getElementById('distanceValue').textContent=formatNumber(distance);
    document.getElementById('refillValue').textContent=formatNumber(refills);
    document.getElementById('gallonsValue').textContent=formatNumber(usedGallons);
    rangeVisual.replaceChildren();
    let remaining=distance;
    while(remaining>0){
      const piece=Math.min(remaining,500);
      const segment=document.createElement('span');
      segment.className='lab__segment';
      segment.style.flexGrow=String(piece);
      segment.style.flexBasis='0';
      rangeVisual.appendChild(segment);
      remaining-=piece;
    }
  }
  function apply(){
    document.documentElement.lang=language==='pt'?'pt-BR':language;
    langSelect.value=language;
    document.title=translations[language].pageTitle;
    document.querySelectorAll('[data-i18n]').forEach(element=>{
      const copy=translations[language][element.dataset.i18n];
      if(typeof copy==='string')element.textContent=copy;
    });
    updateRange();
    document.dispatchEvent(new Event('fuel:language-change'));
  }
  langSelect.addEventListener('change',event=>{
    if(!supported.includes(event.target.value))return;
    language=event.target.value;
    try{localStorage.setItem('fuel-route-language-v2',language);}catch(_){}
    apply();
  });
  slider?.addEventListener('input',updateRange);
  apply();
})();