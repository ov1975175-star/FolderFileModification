import os, gc
import UnityPy
from UnityPy.classes.math import ColorRGBA

EXCLUDE_WORDS=["hair","shoe","accessory","accessor"]
EXCLUDE_WALLS=["icewall","wall","barrier","shield","fence","gate","door","block","gloo","ice","bunker","pared"]

V4={
    "name":"dolflexff","shader_file_id":1,"shader_path_id":7146432734730272451,
    "shader_keywords":"_TINTCOLOR_ON","lightmap_flags":4,"enable_instancing":False,
    "double_sided_gi":False,"custom_render_queue":3001,
    "floats":{"_ColorMask":15.0,"_ColorMask2":14.0,"_Cull":0.0,"_CutOff":0.5,"_DestAlpha":1.0,
              "_EmissiveR":0.0,"_FadeFactor":1.0,"_InvFade":1.0,"_RGBAlpha":0.0,"_SourceAlpha":5.0,
              "_ZTest":8.0,"_ZTestMode":8.0,"_ZWrite2":0.0},
    "colors":{
        "_Color_DisTex":(0,0.5,1,1),"_Color_Tex":(0,0.5,1,1),"_Mask_Dis":(0,0.5,1,1),
        "_TintColor":(0,0.5,1,1),"_UVAnimdistex":(0,0.5,1,1),"_UVAnimtex":(0,0.5,1,5),
        "__NULL_Angle_Intensity_Power_Dissolve_MAX":(1,50,0,10),
        "__NULL_Angle_Intensity_Power_Dissolve_MIN":(0,0.5,1,1),
        "__NULL_MaskEnable_Check":(0,0.4,1,1),
        "__NULL_UserMode_RenderMode_AlphaMode_DistortEnable":(0,0.4,1,1),
    }
}

def is_wall(name): return any(x in name.lower() for x in EXCLUDE_WALLS)

def apply_v4(data):
    data.m_Name=V4["name"]
    data.m_Shader.m_FileID=V4["shader_file_id"]
    data.m_Shader.m_PathID=V4["shader_path_id"]
    data.m_ShaderKeywords=V4["shader_keywords"]
    data.m_LightmapFlags=V4["lightmap_flags"]
    data.m_EnableInstancingVariants=V4["enable_instancing"]
    data.m_DoubleSidedGI=V4["double_sided_gi"]
    data.m_CustomRenderQueue=V4["custom_render_queue"]
    sp=data.m_SavedProperties
    sp.m_Floats=list(V4["floats"].items())
    nc=[]
    for k,(r,g,b,a) in V4["colors"].items():
        col=ColorRGBA();col.r=r;col.g=g;col.b=b;col.a=a;nc.append((k,col))
    sp.m_Colors=nc

def deep_scan(obj):
    cambios=0
    if isinstance(obj,dict):
        for k in obj: obj[k],c=deep_scan(obj[k]);cambios+=c
    elif isinstance(obj,list):
        for i in range(len(obj)): obj[i],c=deep_scan(obj[i]);cambios+=c
    elif isinstance(obj,float):
        if obj==1.0: return 3000.0,1
    return obj,cambios

def mod_charector(src_dir, dst_dir):
    """Returns (mat_count, antena_count)"""
    cm=cant=0
    files=[f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir,f))]
    for fname in files:
        sp=os.path.join(src_dir,fname)
        dp=os.path.join(dst_dir,fname)
        try:
            env=UnityPy.load(sp)
            for obj in env.objects:
                if obj.type.name=="Material":
                    try:
                        data=obj.read();name=str(data.m_Name)
                        if name.upper().startswith("VFX") or is_wall(name):continue
                        apply_v4(data);data.save();cm+=1
                    except:pass
                elif obj.type.name=="MonoBehaviour":
                    try:
                        data=obj.read_typetree();name=str(data.get("m_Name","")).lower()
                        if not(name.startswith("male_") or name.startswith("female_")):continue
                        if any(x in name for x in EXCLUDE_WORDS):continue
                        nd,c=deep_scan(data)
                        if c>0: obj.save_typetree(nd);cant+=1
                    except:pass
            with open(dp,"wb") as f:f.write(env.file.save())
            del env;gc.collect()
        except:pass
    return cm,cant
