import torch
import numpy as np
from subprocess import check_output
import os
import pyexr
import scipy.misc
ROOT = "E:/WebStorm Projects/3dscene-midterm/suncg/object"
objectns = []
icosavn = np.loadtxt("./cubevn", dtype=np.float)
icosavn = torch.from_numpy(icosavn).float().to("cuda")
render_name = 'render6orth'
max_tolerance = 16.0
for name in os.listdir(ROOT):
    if os.path.exists(ROOT + "/{}/{}.obj".format(name, name)):
        objectns.append(name)
def AABB(objpath):
    vertices = []
    with open(objpath) as objf:
        for line in objf:
            if line.startswith("#"): continue
            values = line.split()
            if len(values) == 0:
                continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                vertices.append([v[0], v[1], v[2]])
    vertices = torch.Tensor(vertices).to('cuda')
    max_p = torch.max(vertices, dim=0)[0]
    min_p = torch.min(vertices, dim=0)[0]
    diag_length = torch.norm(max_p - min_p) * 2.0
    # center = torch.mean(vertices, dim=0)
    center = (max_p + min_p) / 2
    camera_positions = icosavn * diag_length + center
    return camera_positions, center, diag_length.item(), torch.max(torch.abs(vertices), dim=0)[0]
def genXML(camera_positions, center, objname, max_abs):
    temp = open("./renderTemplateCubeOrth")
    temp = temp.read()
    index = 4
    renderids = []
    for d in camera_positions[4:5]:
        with open(ROOT + "/{}/{}/render-{}-{}.xml".format(objname, render_name, objname, index), 'w') as f:
            objpath = ROOT + "/{}/{}.obj".format(objname, objname)
            f.write(temp.format(max_abs[0].item(), max_abs[2].item(),
                d[0], d[1], d[2], center[0], center[1], center[2], '0, 0, 1',
                int(2000 * max_abs[0].item()), int(2000 * max_abs[2].item()),
                objpath))
        renderids.append("render-{}-{}".format(objname, index))
        index = index + 1
    return renderids
for i in range(311, len(objectns)):
    objname = objectns[i]
    objpath = ROOT + "/{}/{}.obj".format(objname, objname)
    thePath = ROOT + "/{}/{}".format(objname, render_name)
    cp, c, diag, max_abs = AABB(objpath)
    if not os.path.exists(thePath):
        os.makedirs(thePath)
    renderids = genXML(cp, c, objname, max_abs)
    for j in range(len(renderids)):
        id = renderids[j]
        c = "C:/Mitsuba/mitsuba.exe " + "\"{}/{}/{}/{}.xml\"".format(ROOT, objname, render_name, id)
        print(c)
        check_output(c, shell=True)
        if id.split("-")[-1] != "d":
            c = "C:/Mitsuba/mtsutil.exe tonemap -o " + "\"{}/{}/{}/{}.png\"".format(ROOT, objname, render_name, id) + \
                " " + \
                "\"{}/{}/{}/{}.exr\"".format(ROOT, objname, render_name, id)
            check_output(c, shell=True)
        elif id.split("-")[-1] == "d":
            file = pyexr.open("{}/{}/{}/{}.exr".format(ROOT, objname, render_name, id))
            d = file.get("distance.Y")
            d = d.reshape(d.shape[0], d.shape[1])
            # d[np.isinf(d)] = 0
            d[d > diag * max_tolerance] = 0
            d = d / np.max(d)
            d = d * 255.0
            scipy.misc.imsave("{}/{}/{}/{}.png".format(ROOT, objname, render_name, id), d)
        print("finish {}".format(id))
