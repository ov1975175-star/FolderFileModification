import os, gc
import UnityPy

def mod_wall_hack(src_dir, dst_dir, mode="trigger"):
    """Returns (saved, skipped)"""
    saved=skipped=0
    files=[f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir,f))]
    for fname in files:
        sp=os.path.join(src_dir,fname)
        dp=os.path.join(dst_dir,fname)
        try:
            env=UnityPy.load(sp);mod=False
            for obj in env.objects:
                if obj.type.name=="MonoScript":
                    try:
                        data=obj.read()
                        name=str(getattr(data,"m_Name",getattr(data,"name",""))).lower()
                        if name=="icewall":
                            obj.set_raw_data(obj.get_raw_data().replace(b"IceWall",b"00000000"))
                            mod=True
                    except:pass
                elif obj.type.name=="BoxCollider":
                    try:
                        tree=obj.read_typetree()
                        changed=False
                        if mode=="mide":
                            if(tree.get("m_Size")!={"x":0.1,"y":0.4,"z":0.1} or
                               tree.get("m_Center")!={"x":0.0,"y":-0.25,"z":0.0}):
                                tree["m_Size"]={"x":0.1,"y":0.4,"z":0.1}
                                tree["m_Center"]={"x":0.0,"y":-0.25,"z":0.0}
                                changed=True
                        else:
                            if not tree.get("m_IsTrigger") or tree.get("m_Enabled")!=False:
                                tree["m_IsTrigger"]=True;tree["m_Enabled"]=False;changed=True
                        if changed:
                            obj.save_typetree(tree);mod=True
                    except:pass
            if mod:
                with open(dp,"wb") as f:f.write(env.file.save())
                saved+=1
            else:
                skipped+=1
            del env;gc.collect()
        except:skipped+=1
    return saved,skipped
