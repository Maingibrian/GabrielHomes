import xml.etree.ElementTree as ET

t = ET.parse('/home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes/static/img/wave-field.svg')
r = t.getroot()
ns = '{http://www.w3.org/2000/svg}'
paths = r.findall(f'.//{ns}path')
print('valid XML,', len(paths), 'paths, viewBox=' + str(r.get('viewBox')))
d = paths[0].get('d').split()
start_y = float(d[1]); end_y = float(d[-1])
print('first path start_y=%.2f end_y=%.2f seam_match=%s' % (start_y, end_y, abs(start_y - end_y) < 0.01))
