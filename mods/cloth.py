import os, gc, tempfile, struct, lzma
import UnityPy
from UnityPy.classes.math import ColorRGBA

EXCLUDE_WORDS = ["hair","shoe","accessory","accessor"]
TINT_R,TINT_G,TINT_B,TINT_A = 0.0,1.0,0.0,1.0

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

def deep_scan(obj):
    cambios=0
    if isinstance(obj,dict):
        for k in obj: obj[k],c=deep_scan(obj[k]); cambios+=c
    elif isinstance(obj,list):
        for i in range(len(obj)): obj[i],c=deep_scan(obj[i]); cambios+=c
    elif isinstance(obj,float):
        if obj==1.0: return 3000.0,1
    return obj,cambios

def apply_antena(in_path,out_path):
    env=UnityPy.load(in_path);total=0
    for obj in env.objects:
        if obj.type.name!="MonoBehaviour":continue
        try:data=obj.read_typetree()
        except:continue
        name=str(data.get("m_Name","")).lower()
        if not(name.startswith("male_") or name.startswith("female_")):continue
        if any(x in name for x in EXCLUDE_WORDS):continue
        new_data,cambios=deep_scan(data)
        if cambios>0:
            try: obj.save_typetree(new_data);total+=cambios
            except: pass
    with open(out_path,"wb") as f:f.write(env.file.save())
    del env;gc.collect()
    return out_path

def modify_ref(ref_path):
    env=UnityPy.load(ref_path);main=None
    for obj in env.objects:
        if obj.type.name!="Material":continue
        d=obj.read()
        name=str(d.m_Name)
        if name in("BRASILEIRO MODS FF","AvatarCommon"):main=d;break
    if main is None:return None
    sp=main.m_SavedProperties;nc=[]
    for k,c in list(sp.m_Colors):
        if k=="_TintColor":
            x=ColorRGBA();x.r=TINT_R;x.g=TINT_G;x.b=TINT_B;x.a=TINT_A;nc.append((k,x))
        else:nc.append((k,c))
    sp.m_Colors=nc;main.save()
    for obj in env.objects:
        if obj.type.name!="Material":continue
        d=obj.read();name=str(d.m_Name)
        if name in("BRASILEIRO MODS FF","AvatarCommon"):continue
        if not name.startswith("Avatar"):continue
        try:
            d.m_Shader.m_FileID=main.m_Shader.m_FileID
            d.m_Shader.m_PathID=main.m_Shader.m_PathID
            d.m_ShaderKeywords=main.m_ShaderKeywords
            d.m_LightmapFlags=main.m_LightmapFlags
            d.m_EnableInstancingVariants=main.m_EnableInstancingVariants
            d.m_DoubleSidedGI=main.m_DoubleSidedGI
            d.m_CustomRenderQueue=main.m_CustomRenderQueue
            sp2=d.m_SavedProperties
            sp2.m_Floats=list(main.m_SavedProperties.m_Floats)
            orig_tex=dict(sp2.m_TexEnvs) if sp2.m_TexEnvs else {}
            nc2=[]
            for k,c in main.m_SavedProperties.m_Colors:
                x=ColorRGBA();x.r=c.r;x.g=c.g;x.b=c.b;x.a=c.a;nc2.append((k,x))
            sp2.m_Colors=nc2
            if orig_tex:sp2.m_TexEnvs=list(orig_tex.items())
            d.save()
        except:pass
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".tmp")
    tmp.write(env.file.save());tmp.close()
    del env;gc.collect()
    return tmp.name

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

def convert(src,dst,ref_tmp):
    raw=open(src,'rb').read();rn0,rn0sz=get_node0(ref_tmp);pos=12
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
    res=bytes(full[sz:]);nf=rn0+res;nd2=lzmac(nf);nnd=bytearray(nd)
    struct.pack_into('>q',nnd,p3+8,rn0sz)
    ncr=(cab[:16]+struct.pack('>I',1)+struct.pack('>I',len(nf))+
         struct.pack('>I',len(nd2))+struct.pack('>H',0x0001)+nnd)
    nc=lzmac(ncr);out=bytearray(raw[:30])
    out+=struct.pack('>q',len(nf))
    out+=struct.pack('>I',len(nc))
    out+=struct.pack('>I',len(ncr))
    out+=struct.pack('>I',0x41)
    out+=nc+nd2
    if len(out)<len(raw):out+=b'\x00'*(len(raw)-len(out))
    open(dst,'wb').write(bytes(out))

def mod_cloth(src_dir, ref_dir, dst_dir):
    """Returns (ok, skip, err)"""
    import tempfile as tf2
    ant_tmp = tf2.mkdtemp()
    ok=skip=err=0
    files=[f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir,f))]
    for f in files:
        src_f=os.path.join(src_dir,f)
        ref_f=os.path.join(ref_dir,f)
        dst_f=os.path.join(dst_dir,f)
        ant_f=os.path.join(ant_tmp,f)
        if not os.path.isfile(ref_f):skip+=1;continue
        try:
            apply_antena(ref_f,ant_f)
            tmp=modify_ref(ant_f)
            if tmp is None:skip+=1;continue
            convert(src_f,dst_f,tmp)
            os.unlink(tmp);ok+=1
        except:err+=1
    # cleanup
    import shutil
    shutil.rmtree(ant_tmp,ignore_errors=True)
    return ok,skip,err
