import dsl
import os

path= os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))+'/setup.cfg'
setup=open(path,'r')
counter=0
for n,line in enumerate(setup.readlines()):
    if 'dsl.services.' in line:
        counter+=1

print counter
print dsl.api.get_services()



# setup=open(os.getcwd()+'/data-services-library/setup.cfg','r')
# for lines in setup.readlines():
#     print lines

#
# def test_get_providers():
#     c=dsl.api.get_providers()
#     assert len(list(c)) == 6
#
# def test_get_services():
#     c=dsl.api.get_services()
#     assert len(list(c)) == 15

