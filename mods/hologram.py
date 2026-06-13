# hologram.py
import os, gc, struct, lzma, tempfile
import UnityPy

PREFIXES=["-3004680475953195993","-8486063","-5522850","7299415","4846455","-4975108"]

MAT={
    "m_Name":"dolflexff","m_Shader":{"m_FileID":1,"m_PathID":-6752853195891321129},
    "m_ShaderKeywords":"_EMISSION","m_LightmapFlags":4,
    "m_EnableInstancingVariants":False,"m_DoubleSidedGI":False,"m_CustomRenderQueue":3001,
    "m_SavedProperties":{
        "m_TexEnvs":[["_MainTex",{"m_Texture":{"m_FileID":2,"m_PathID":-1376813895408464067},
                                   "m_Scale":{"x":1,"y":1},"m_Offset":{"x":0,"y":0}}]],
        "m_Floats":[["_ColorMask",15],["_ColorMask2",14],["_Cull",0],["_CutOff",0.5],
                    ["_DestAlpha",1],["_EmissiveR",0],["_FadeFactor",1],["_InvFade",1],
                    ["_RGBAlpha",0],["_SourceAlpha",5],["_ZTest",8],["_ZTestMode",8],["_ZWrite2",0]],
        "m_Colors":[
            ["_Color_DisTex",{"r":1,"g":0,"b":0,"a":1}],
            ["_Color_Tex",{"r":1,"g":0,"b":0,"a":1}],
            ["_Mask_Dis",{"r":1,"g":0,"b":0,"a":1}],
            ["_TintColor",{"r":1,"g":0,"b":0,"a":1}],
            ["_UVAnimdistex",{"r":1,"g":0,"b":0,"a":1}],
            ["_UVAnimtex",{"r":1,"g":0,"b":0,"a":5}],
            ["__NULL_Angle_Intensity_Power_Dissolve_MAX",{"r":1,"g":50,"b":1,"a":10}],
            ["__NULL_Angle_Intensity_Power_Dissolve_MIN",{"r":1,"g":0,"b":0,"a":1}],
            ["__NULL_MaskEnable_Check",{"r":1,"g":0,"b":0,"a":1}],
            ["__NULL_UserMode_RenderMode_AlphaMode_DistortEnable",{"r":1,"g":1,"b":1,"a":1}]
        ]
    }
}

def is_target(pid): return any(str(pid).startswith(p) for p in PREFIXES)

def lz4d(data,mx):
    out=bytearray();pos=0
    while pos<len(data) and len(out)<mx:
        try:
            t=data[pos];pos+=1;ll=(t>>4)&0xF
            if ll==15:
                while 1:
                    e=data[pos];pos+=1;ll+=e
                    if e!=255:break
            out.extend(data[pos:pos+ll]);pos+=ll
            if pos>=len(data):break
            off=data[pos]|(data[pos+1]<<8);pos+=2
            if off==0:break
            ml=(t&0xF)+4
            if(t&0xF)==15:
                while 1:
                    e=data[pos];pos+=1;ml+=e
                    if e!=255:break
            mp=len(out)-off
            for i in range(ml):out.append(out[mp+i])
        except:break
    return bytes(out)

def lzmac(data,lc=3,lp=0,pb=2,ds=8388608):
    p=bytes([lc+lp*9+pb*45])+struct.pack('<I',ds)
    return p+lzma.compress(data,format=lzma.FORMAT_RAW,
        filters=[{'id':lzma.FILTER_LZMA1,'lc':lc,'lp':lp,'pb':pb,'dict_size':ds}])

def lzmad(data):
    p=data[:5]
    return lzma.decompress(data[5:],format=lzma.FORMAT_RAW,
        filters=[{'id':lzma.FILTER_LZMA1,'lc':p[0]%9,'lp':(p[0]//9)%5,
                  'pb':p[0]//45,'dict_size':struct.unpack('<I',p[1:5])[0]}])

def decomp(data,ci,ui,comp):
    blk=data[:ci]
    if comp in(2,3):return lz4d(blk,ui)
    elif comp==1:return lzmad(blk)
    else:return blk[:ui]

def get_node0(path):
    b=open(path,'rb').read();pos=12
    while b[pos]!=0:pos+=1
    pos+=1
    while b[pos]!=0:pos+=1
    pos+=9
    ci=struct.unpack('>I',b[pos:pos+4])[0];pos+=4
    ui=struct.unpack('>I',b[pos:pos+4])[0];pos+=4
    fl=struct.unpack('>I',b[pos:pos+4])[0];pos+=4
    cab=decomp(b[pos:],ci,ui,fl&0x3F)
    p2=16;nb=struct.unpack('>I',cab[p2:p2+4])[0];p2+=4;blks=[]
    for i in range(nb):
        u=struct.unpack('>I',cab[p2:p2+4])[0];p2+=4
        c=struct.unpack('>I',cab[p2:p2+4])[0];p2+=4
        f=struct.unpack('>H',cab[p2:p2+2])[0];p2+=2
        blks.append((u,c,f&0x3F))
    full=bytearray();dp=pos+ci
    for u,c,f in blks:full.extend(decomp(b[dp:],c,u,f));dp+=c
    p2+=4;sz=struct.unpack('>q',cab[p2+8:p2+16])[0]
    return bytes(full[:sz]),sz

def merge_save(src,tmp_path,dst):
    raw=open(src,'rb').read();orig=len(raw)
    rn0,rn0sz=get_node0(tmp_path)
    pos=12
    while raw[pos]!=0:pos+=1
    pos+=1
    while raw[pos]!=0:pos+=1
    pos+=9
    ci=struct.unpack('>I',raw[pos:pos+4])[0];pos+=4
    ui=struct.unpack('>I',raw[pos:pos+4])[0];pos+=4
    fl=struct.unpack('>I',raw[pos:pos+4])[0];pos+=4;he=pos
    cab=decomp(raw[he:],ci,ui,fl&0x3F)
    p2=16;nb=struct.unpack('>I',cab[p2:p2+4])[0];p2+=4;blks=[]
    for i in range(nb):
        u=struct.unpack('>I',cab[p2:p2+4])[0];p2+=4
        c=struct.unpack('>I',cab[p2:p2+4])[0];p2+=4
        f=struct.unpack('>H',cab[p2:p2+2])[0];p2+=2
        blks.append((u,c,f&0x3F))
    nd=cab[p2:];full=bytearray();dp=he+ci
    for u,c,f in blks:full.extend(decomp(raw[dp:],c,u,f));dp+=c
    p3=4;sz=struct.unpack('>q',nd[p3+8:p3+16])[0]
    rest=bytes(full[sz:]);nf=rn0+rest;nd2=lzmac(nf);nnd=bytearray(nd)
    struct.pack_into('>q',nnd,p3+8,rn0sz)
    ncr=(cab[:16]+struct.pack('>I',1)+struct.pack('>I',len(nf))+
         struct.pack('>I',len(nd2))+struct.pack('>H',0x0001)+nnd)
    nc=lzmac(ncr)
    out=bytearray(raw[:30])
    out+=struct.pack('>q',len(nf))
    out+=struct.pack('>I',len(nc))
    out+=struct.pack('>I',len(ncr))
    out+=struct.pack('>I',0x41)
    out+=nc+nd2
    if len(out)<orig:out+=b'\x00'*(orig-len(out))
    elif len(out)>orig:out=out[:orig]
    open(dst,'wb').write(bytes(out))

def mod_hologram(src_dir, dst_dir):
    """Returns (done, skipped)"""
    done=skip=0
    files=[f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir,f))]
    for fname in files:
        sp=os.path.join(src_dir,fname)
        dp=os.path.join(dst_dir,fname)
        try:
            env=UnityPy.load(sp);inj=0
            for obj in env.objects:
                if not is_target(obj.path_id):continue
                try:
                    tree=obj.read_typetree()
                    tree["m_Name"]=MAT["m_Name"]
                    tree["m_Shader"]=MAT["m_Shader"]
                    tree["m_ShaderKeywords"]=MAT["m_ShaderKeywords"]
                    tree["m_LightmapFlags"]=MAT["m_LightmapFlags"]
                    tree["m_EnableInstancingVariants"]=MAT["m_EnableInstancingVariants"]
                    tree["m_DoubleSidedGI"]=MAT["m_DoubleSidedGI"]
                    tree["m_CustomRenderQueue"]=MAT["m_CustomRenderQueue"]
                    sp2=tree.get("m_SavedProperties",{})
                    sp2["m_TexEnvs"]=MAT["m_SavedProperties"]["m_TexEnvs"]
                    sp2["m_Floats"]=MAT["m_SavedProperties"]["m_Floats"]
                    sp2["m_Colors"]=MAT["m_SavedProperties"]["m_Colors"]
                    tree["m_SavedProperties"]=sp2
                    obj.save_typetree(tree);inj+=1
                except:pass
            if inj==0:
                del env;gc.collect();skip+=1;continue
            tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".tmp")
            tmp.write(env.file.save());tmp.close()
            del env;gc.collect()
            merge_save(sp,tmp.name,dp)
            os.unlink(tmp.name);done+=1
        except:skip+=1
    return done,skip
