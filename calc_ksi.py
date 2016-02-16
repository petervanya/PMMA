#!/usr/bin/env python
"""
[AD HOC] Script to calculate ksi parameters at 300 K of
* PMMA-water
* PMMA-methanol
12/02/16
"""
from math import sqrt
R = 8.314
T = 300

rho_water = 1000
rho_meth = 792
rho_PMMA = 1180

m_PMMA = (5*12 + 2*16 + 8*1)/1000.
m_water = (2*1 + 16)/1000.
m_meth = (16 + 12 + 4*1)/1000.

# in cm**3/mol
Vm_PMMA = m_PMMA/rho_PMMA * 1e6
Vm_water = m_water/rho_water * 1e6
Vm_meth = m_meth/rho_meth * 1e6

# in MPa**0.5
delta_PMMA = 19
delta_water = 47.8
# delta_meth = sqrt(9.87**2 + 6.37**2 + 5.86**2) 
# from http://www.wag.caltech.edu/publications/sup/pdf/587.pdf
delta_meth = 29.7

ksi_PW = (Vm_PMMA + Vm_water)/(2*R*T)*(delta_PMMA - delta_water)**2
ksi_PM = (Vm_PMMA + Vm_meth) /(2*R*T)*(delta_PMMA - delta_meth)**2

print "Solubility params: PMMA = %f | water = %f | meth = %f" % (delta_PMMA, delta_water, delta_meth)
print "Ksi PMMA-water = %.3f" % ksi_PW
print "Ksi PMMA-methanol = %.3f" % ksi_PM
