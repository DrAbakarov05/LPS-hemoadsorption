/**
 * Build two editable PowerPoint slides with @oai/artifact-tool.
 * 1. Every line, tick, number and curve is an individually named native object.
 * 2. Same graph with removable annotations as separate textboxes.
 *
 * In the Codex primary runtime, copy this module to a private directory with
 * node_modules linked to CODEX_PRIMARY_RUNTIME_NODE_MODULES, then run:
 * node build_powerpoint.mjs /absolute/path/to/figures/sepsis_global
 * First run plot_sepsis.py. No network requests are made by this builder.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root=path.resolve(process.argv[2]);
const stage=path.resolve(process.argv[3] || path.join(root,'../../..','tmp_ppt_build'));
await fs.mkdir(stage,{recursive:true});
const scene=JSON.parse(await fs.readFile(path.join(root,'output/editable_scene.json'),'utf8'));
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const font=scene.style.font_family;
const invisible={style:'solid',fill:'none',width:0};

function addText(slide,it){
  const shape=slide.shapes.add({geometry:'textbox',name:it.name,
    position:{left:it.left,top:it.top,width:it.width,height:it.height},fill:'none',line:invisible});
  shape.text=it.text;
  shape.text.style={typeface:font,fontSize:it.size,color:it.color,bold:it.bold,
    alignment:it.align,verticalAlignment:'top',insets:0,wrap:false};
}
function addItem(slide,it){
  if(it.kind==='text')return addText(slide,it);
  if(it.kind==='line'){
    const xs=it.points.map(p=>p[0]),ys=it.points.map(p=>p[1]);
    const left=Math.min(...xs),top=Math.min(...ys);
    const w=Math.max(1,Math.max(...xs)-left),h=Math.max(1,Math.max(...ys)-top);
    const commands=it.points.map((p,i)=>({[i?'lineTo':'moveTo']:{x:p[0]-left,y:p[1]-top}}));
    slide.shapes.add({geometry:'custom',name:it.name,position:{left,top,width:w,height:h},
      fill:'none',line:{style:it.dash?'dashed':'solid',fill:it.color,width:it.width},
      customPaths:[{width:w,height:h,commands}]});
  }else if(it.kind==='rect'){
    slide.shapes.add({geometry:'rect',name:it.name,
      position:{left:it.left,top:it.top,width:it.width,height:it.height},
      fill:'none',line:{style:'solid',fill:it.color,width:it.line_width}});
  }else if(it.kind==='circle'){
    slide.shapes.add({geometry:'ellipse',name:it.name,
      position:{left:it.cx-it.radius,top:it.cy-it.radius,width:it.radius*2,height:it.radius*2},
      fill:it.color,line:{style:'solid',fill:'white',width:1}});
  }
}
const notes=`Sources: GBD 2021 Global Sepsis Collaborators. Lancet Glob Health 2025;13:e2013-e2026. DOI:10.1016/S2214-109X(25)00356-0, Supplementary appendix 1, Table S6. Absolute deaths, all ages, worldwide, 1990-2021.\nWoo HG et al. Critical Care 2026;30:288. DOI:10.1186/s13054-026-06024-7, Figure 2A. Age-standardized rate among adults >=20 in 79 countries, explicit sepsis underlying/primary cause. Historical through 2023, forecast from 2024. Published anchors: 2000 9.15; 2023 12.77; 2050 20.32. The other 48 annual rate points are approximate digitization of the published central curve, not the authors' raw annual data.\nThe studies have different populations and case definitions. Do not convert the ASR into global counts or infer a single continued series. Forecast shown dashed. Confidence intervals and country trajectories omitted.\nWHO characterized the outbreak as a pandemic on 2020-03-11. The red outline groups annual estimates 2020 and 2021; its edges are year-bin boundaries, not exact event dates. Uniform year-to-position mapping from 1990 to 2050.\nEditing: use the Selection Pane to select named shapes on slides 1-2. Curves are native freeform paths with editable points; all axis labels are text. Numerical changes can be made in the source CSV then regenerated; curves are native editable freeform objects.`;
for(const annotated of [false,true]){
  const slide=presentation.slides.add();slide.background.fill='white';
  for(const item of scene.core)addItem(slide,item);
  if(annotated)for(const item of scene.annotations)addItem(slide,item);
  slide.speakerNotes.text=notes;
}

for(let i=0;i<presentation.slides.items.length;i++){
  const blob=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1.5});
  await fs.writeFile(path.join(stage,`slide_${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const candidate=path.join(stage,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL('/root/.codex/skills/builtins/presentations/container_tools/artifact_tool_utils.mjs').href);
const result=await finalizePresentation({
  workspaceDir:path.resolve(root,'../../..'),candidatePath:candidate,
  finalPath:path.join(root,'output/sepsis_combined_editable.pptx'),
  pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
  integrityValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_package_integrity.py',
  layoutValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_layout_geometry.py',
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
  explicitTotalSlideCount:2,requiredNativeChartOwnerSlides:[],requiredNativeTableOwnerSlides:[],
  fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
  receiptPath:path.join(stage,'validation.json')
});
console.log(JSON.stringify(result));
