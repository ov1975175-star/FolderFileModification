import os

def mod_fileinfo(fileinfo_path, mod_folder):
    """Returns change count"""
    with open(fileinfo_path,"r") as f:
        lines=f.readlines()
    sizes={}
    for fname in os.listdir(mod_folder):
        p=os.path.join(mod_folder,fname)
        if os.path.isfile(p):
            sizes[fname.split(".")[0]]=os.path.getsize(p)
    new_lines=[];changes=0
    for line in lines:
        parts=line.strip().split(",")
        if len(parts)>=3 and parts[0] in sizes:
            parts[2]=str(sizes[parts[0]])
            new_lines.append(",".join(parts)+"\n")
            changes+=1
        else:
            new_lines.append(line)
    with open(fileinfo_path,"w") as f:
        f.writelines(new_lines)
    return changes
