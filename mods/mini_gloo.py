import os, gc
import UnityPy

def mod_mini_gloo(src_dir, dst_dir):
    """Returns (saved, skipped)"""
    saved=skipped=0
    files=[f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir,f))]
    for fname in files:
        sp=os.path.join(src_dir,fname)
        dp=os.path.join(dst_dir,fname)
        try:
            env=UnityPy.load(sp)
            objs={o.path_id:o for o in env.objects}
            mod=False
            for obj in env.objects:
                if obj.type.name=="GameObject":
                    try:
                        tree=obj.read_typetree();name=tree.get("m_Name","");low=name.lower()
                        if("icewall_bunker_new" in low and low!="icewall_bunker_new" and "preview" not in low):
                            for ci in tree.get("m_Component",[]):
                                pid=ci["component"]["m_PathID"]
                                if pid in objs and objs[pid].type.name=="Transform":
                                    trans=objs[pid].read_typetree()
                                    for a in ["x","y","z"]:
                                        trans["m_LocalPosition"][a]=0.466666
                                        trans["m_LocalScale"][a]=0.466666
                                    objs[pid].save_typetree(trans);mod=True
                    except:pass
            if mod:
                with open(dp,"wb") as f:f.write(env.file.save())
                saved+=1
            else:
                skipped+=1
            del env;gc.collect()
        except:skipped+=1
    return saved,skipped
