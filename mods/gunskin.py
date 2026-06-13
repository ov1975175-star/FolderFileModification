import os, gc, shutil
import UnityPy
from UnityPy.classes.math import ColorRGBA

V4 = {
    "name":"dolflexff","shader_file_id":1,"shader_path_id":7146432734730272451,
    "shader_keywords":"_TINTCOLOR_ON","lightmap_flags":4,"enable_instancing":False,
    "double_sided_gi":False,"custom_render_queue":3001,
    "floats":{"_ColorMask":15,"_ColorMask2":14,"_Cull":0,"_CutOff":0.5,"_DestAlpha":1,
              "_EmissiveR":0,"_FadeFactor":1,"_InvFade":1,"_RGBAlpha":0,"_SourceAlpha":5,
              "_ZTest":8,"_ZTestMode":8,"_ZWrite2":0},
    "colors":{
        "_Color_DisTex":(0,0.5,1,1),"_Color_Tex":(0,0.5,1,1),"_Mask_Dis":(0,0.5,1,1),
        "_TintColor":(0,0.5,1,1),"_UVAnimdistex":(0,0.5,1,1),"_UVAnimtex":(0,0.5,1,5),
        "__NULL_Angle_Intensity_Power_Dissolve_MAX":(1,50,0,10),
        "__NULL_Angle_Intensity_Power_Dissolve_MIN":(0,0.5,1,1),
        "__NULL_MaskEnable_Check":(0,0.4,1,1),
        "__NULL_UserMode_RenderMode_AlphaMode_DistortEnable":(0,0.4,1,1),
    }
}

GLOO = {**V4,
    "floats":{**V4["floats"],"_ZTest":4,"_ZTestMode":4},
    "colors":{
        "_Color_DisTex":(1,0.5,0,0.1),"_Color_Tex":(1,0.5,0,0.1),"_Mask_Dis":(1,0.5,0,0.1),
        "_TintColor":(1,0.5,0,0.1),"_UVAnimdistex":(1,0.5,0,0.1),"_UVAnimtex":(1,0.5,0,5),
        "__NULL_Angle_Intensity_Power_Dissolve_MAX":(1,50,0,10),
        "__NULL_Angle_Intensity_Power_Dissolve_MIN":(1,0.5,0,0.1),
        "__NULL_MaskEnable_Check":(1,0.4,0,0.1),
        "__NULL_UserMode_RenderMode_AlphaMode_DistortEnable":(1,0.4,0,0.1),
    }
}

WALL_KW = ["wall","gloo","ice","icewall","bunker","new","icewallbunker","pared"]

def is_wall(name): return any(k in name.lower() for k in WALL_KW)

def apply_preset(data, p):
    data.m_Name=p["name"]
    data.m_Shader.m_FileID=p["shader_file_id"]
    data.m_Shader.m_PathID=p["shader_path_id"]
    data.m_ShaderKeywords=p["shader_keywords"]
    data.m_LightmapFlags=p["lightmap_flags"]
    data.m_EnableInstancingVariants=p["enable_instancing"]
    data.m_DoubleSidedGI=p["double_sided_gi"]
    data.m_CustomRenderQueue=p["custom_render_queue"]
    sp=data.m_SavedProperties
    sp.m_Floats=list(p["floats"].items())
    nc=[]
    for k,(r,g,b,a) in p["colors"].items():
        c=ColorRGBA();c.r=r;c.g=g;c.b=b;c.a=a;nc.append((k,c))
    sp.m_Colors=nc

def mod_gunskin(src_dir, dst_dir):
    """Returns (v4_count, gloo_count)"""
    cm=cg=0
    files=[f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir,f))]
    for fname in files:
        sp=os.path.join(src_dir,fname)
        dp=os.path.join(dst_dir,fname)
        shutil.copy2(sp,dp)
        try:
            env=UnityPy.load(dp)
            for obj in env.objects:
                if obj.type.name!="Material":continue
                data=obj.read();name=str(data.m_Name)
                if name.upper().startswith("VFX"):continue
                if is_wall(name): apply_preset(data,GLOO);cg+=1
                else: apply_preset(data,V4);cm+=1
                data.save()
            with open(dp,"wb") as f:f.write(env.file.save())
            del env;gc.collect()
        except:pass
    return cm,cg
