import torch
import numpy as np
from subprocess import check_output
import os
import pyexr
import scipy.misc
import json
ROOT = "E:/WebStorm Projects/3dscene-midterm/suncg/object"
objectns = []
icosavn = np.loadtxt("./icosavn", dtype=np.float)
icosavn = torch.from_numpy(icosavn).float().to("cuda")
max_tolerance = 16.0
for name in os.listdir(ROOT):
    if os.path.exists(ROOT + "/{}/{}.obj".format(name, name)):
        # objectns.append(ROOT + "/{}/{}.obj".format(name, name))
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
    diag_length = torch.norm(max_p - min_p) * 2.5
    center = torch.mean(vertices, dim=0)
    camera_positions = icosavn * diag_length + center
    return camera_positions, center, diag_length.item()
def genXML(camera_positions, center, objname):
    temp = open("./renderTemplate")
    temp = temp.read()
    tempD = open("./renderTemplateD")
    tempD = tempD.read()
    index = 0
    renderids = []
    for d in camera_positions:
        with open(ROOT + "/{}/render20/render-{}-{}.xml".format(objname, objname, index), 'w') as f:
            objpath = ROOT + "/{}/{}.obj".format(objname, objname)
            f.write(temp.format(d[0], d[1], d[2], center[0], center[1], center[2], objpath))
        renderids.append("render-{}-{}".format(objname, index))
        with open(ROOT + "/{}/render20/render-{}-{}-d.xml".format(objname, objname, index), 'w') as f:
            objpath = ROOT + "/{}/{}.obj".format(objname, objname)
            f.write(tempD.format(d[0], d[1], d[2], center[0], center[1], center[2], objpath))
        renderids.append("render-{}-{}-d".format(objname, index))
        index = index + 1
    return renderids
def genJson(objname):
    objpath = ROOT + "/{}/{}.obj".format(objname, objname)
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
    diag_length = torch.norm(max_p - min_p) * 2.5
    center = torch.mean(vertices, dim=0)
    camera_positions = icosavn * diag_length + center
    for index in range(len(camera_positions)):
        d = camera_positions[index]
        j = dict()
        j['max'] = max_p.tolist()
        j['min'] = min_p.tolist()
        j['diag'] = diag_length.tolist()
        j['center'] = center.tolist()
        j["cameraPos"] = d.tolist()
        j['icosavn'] = icosavn[index].tolist()
        j['max_tolerance'] = max_tolerance
        file = pyexr.open("{}/{}/render20/render-{}-{}-d.exr".format(ROOT, objname, objname, index))
        d = file.get("distance.Y")
        d = d.reshape(d.shape[0], d.shape[1])
        d[d > diag * max_tolerance] = 0
        j['maxDepth'] = np.max(d).item()
        with open("{}/{}/render20/render-{}-{}.json".format(ROOT, objname, objname, index), 'w') as f:
            json.dump(j, f)
# for i in range(len(objectns)):
#     print(i, objectns[i])
for i in range(676, len(objectns)):
    objname = objectns[i]
    objpath = ROOT + "/{}/{}.obj".format(objname, objname)
    thePath = ROOT + "/{}/render20".format(objname)
    cp, c, diag = AABB(objpath)
    if not os.path.exists(thePath):
        os.makedirs(thePath)
    renderids = genXML(cp, c, objname)
    for j in range(len(renderids)):
        id = renderids[j]
        c = "C:/Mitsuba/mitsuba.exe " + "\"{}/{}/render20/{}.xml\"".format(ROOT, objname, id)
        print(c)
        check_output(c, shell=True)
        if id.split("-")[-1] != "d":
            c = "C:/Mitsuba/mtsutil.exe tonemap -o " + "\"{}/{}/render20/{}.png\"".format(ROOT, objname, id) + " " + \
                "\"{}/{}/render20/{}.exr\"".format(ROOT, objname, id)
            check_output(c, shell=True)
        elif id.split("-")[-1] == "d":
            file = pyexr.open("{}/{}/render20/{}.exr".format(ROOT, objname, id))
            d = file.get("distance.Y")
            d = d.reshape(d.shape[0], d.shape[1])
            # d[np.isinf(d)] = 0
            d[d > diag * max_tolerance] = 0
            d = d / np.max(d)
            d = d * 255.0
            scipy.misc.imsave("{}/{}/render20/{}.png".format(ROOT, objname, id), d)
        print("finish {}".format(id))
    genJson(objname)
