import Template,os

distpath = os.getcwd()
t = Template.Template("linkcheck/__init__.py.tmpl")
f = open("linkcheck/__init__.py","w")
f.write(t.fill_in({"install_data": distpath}))
f.close()
t = Template.Template("linkchecker.tmpl")
f = open("linkchecker","w")
f.write(t.fill_in({"syspath": "sys.path.insert(0, '"+distpath+"')"}))
f.close()
os.chmod("linkchecker", 0755)
t = Template.Template("linkchecker.bat.tmpl")
f = open("linkchecker.bat","w")
f.write(t.fill_in({"install_scripts": distpath}))
f.close()
print "Local installation ok"
