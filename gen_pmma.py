#!/usr/bin/env python
"""Usage:
    gen_pmma.py <input> [--density <rho>] [--save <fname>] [--xyz <xyz>]

Generate LAMMPS input file to simulate PMMA with water.

Parameters:
    <input>          input yaml file

Options:
    --density <rho>  "dpd" or "real" (based on real data) [default: dpd]
    --save <fname>   Output file name
    --xyz <xyz>      Produce xyz file

pv278@cam.ac.uk, 03/02/15
"""
import numpy as np
from math import *
from docopt import docopt
import sys, yaml
import lmp_lib as ll
import parse_topo as pt

kB = 1.38e-23
NA = 6.022e23
Maw = 1.67e-27

rc = 8.14e-10
mw = 6*18
m0 = 6*18*Maw    # 6 water molecules in a bead
a_ii = 25

elem_wts = yaml.load(open(sys.path[0]+"/atomic_weights.yaml").read())
rho_PMMA = 1180
rho_water = 1000
rho_DPD = 3 / rc**3


def pmma_bead_mass():
    """Return mass of one PMMA monomer, defining a DPD bead"""
    return 5*elem_wts["C"] + 2*elem_wts["O"] + 8*elem_wts["H"]


def num_chains(rho, L, n):
    """Find number of chains in a given volume at a given density,
    Nc*n*pmma_bead_mass() = rho_PMMA*V
    return Nc"""
    Nc = rho_PMMA * L**3 / (n*pmma_bead_mass())
    return Nc


def grow_polymer(L, n, Nc, mu=1.0, sigma=0.1):
    """Generate coordinates of matrix polymer chains
    return (5, n*Nc) matrix, columns: [mol_ids, bead_type, xyz]
    Input:
    * L: cubic box size
    * n: polymerisation
    * Nc: number of chains
    * mu: mean of bead distance
    * sigma: deviation of bead distance"""
    xyz = np.zeros((Nc*n, 5))
    atom_ids = np.matrix(np.ones(n)).T
    for i in range(Nc):
        xyz[i*n : (i+1)*n] = np.hstack(( (i+1)*atom_ids,\
                                         atom_ids,\
                                         grow_one_chain(L, n, Nc, mu, sigma) ))
    return xyz


def grow_one_chain(L, n, Nc, mu, sigma):
    """Return (3,n) xyz matrix of one chain"""
    xyz = np.zeros((n, 3))
    xyz[0] = np.random.rand(3)*L
    for i in range(1, n):
        theta = np.random.rand()*pi
        phi = np.random.rand()*2*pi
        r = mu + np.random.randn()*L*sigma
        new_bead_pos = [r*cos(theta), r*sin(theta)*cos(phi), r*sin(theta)*sin(phi)]
        xyz[i] = xyz[i-1] + new_bead_pos
        xyz[i] = np.where(xyz[i] > L, L, xyz[i])       # set coord to L or 0 on the boundary
        xyz[i] = np.where(xyz[i] < 0.0, 0.0, xyz[i])
    return xyz


def create_bonds(n, Nc):
    """Create bond matrix
    return (n*Nc, 3) matrix, columns: [bond_type, atom1, atom2]"""
    mat = np.zeros(((n-1)*Nc, 3), dtype=int)
    for i in range(Nc):
        one_chain_bonds = np.hstack(( np.matrix([1]*(n-1)).T,\
                                      np.matrix( np.arange(n*i+1, n*(i+1)) ).T,\
                                      np.matrix( np.arange(n*i+2, n*(i+1)+1) ).T ))
        mat[i*(n-1) : (i+1)*(n-1)] = one_chain_bonds
    return mat


def gen_water_beads(L, Nw, count=1):
    """Generate xyz matrix from a given number of water beads.
    Return (5, Nw) matrix, columns: [mol_id, bead_type, xyz]
    * count: where to start molecular id counting"""
    xyz = np.zeros((Nw, 5))
    xyz[:, 2:5] = np.random.rand(Nw, 3)*L
    xyz[:, 1] = 2
    xyz[:, 0] = range(count, count+Nw)
    return xyz


def gen_pair_coeffs(bead_types, ksi_params_yaml, gamma, rc):
    """
    PROVISIONAL
    Generate atomic params a_ij for all possible combinations 
    given number of atom types. Read custom bonds from input.yaml file
    Nafion bead_types = "ABCW"
    """
    a_ij = {}
    Nbt = len(bead_types)
    num2coeff = dict((num, coeff) for (num, coeff) in zip(range(1, Nbt+1), bead_types))
    for i in range(1, Nbt+1):
        for j in range(1, i+1):
            key = "%i %i" % (j, i)
            lkey = "%s %s" % (num2coeff[j], num2coeff[i])
            if lkey in ksi_params_yaml.keys() or lkey[::-1] in ksi_params_yaml.keys():
                try:
                    a_ij[key] = [(a_ii + 3.27*ksi_params_yaml[lkey]) * kB*T/rc, gamma, rc]
                except KeyError: # "B A" -> "A B"
                    a_ij[key] = [(a_ii + 3.27*ksi_params_yaml[lkey[::-1]]) * kB*T/rc, gamma, rc]
            else:
                a_ij[key] = [a_ii * kB*T/rc, gamma, rc]
    return a_ij


def gen_bond_coeffs(bead_types, bonds_yaml, r0):
    """
    PROVISIONAL
    Generate bond coeffs k_ij and r0 for all possible combinations
    given number of atom types. Read custom bonds from input.yaml file
    """
    k_ij = {}
    bmap = pt.bond_map(bead_types)   # "AW", TOO COMPLICATED
    Nbt = len(bead_types)
    for i in range(Nbt):
        for j in range(i+1): 
            key = bead_types[i] + " " + bead_types[j]
            if key in bonds_yaml.keys():
                k_ij[bmap[key]] = [bonds_yaml[key] * kB*T/(rc**2), r0]
            else:
                k_ij[bmap[key]] = [4 * kB*T/(rc**2), r0]   # default interaction
    return k_ij


if __name__ == "__main__":
    args = docopt(__doc__)
    try:
        data = yaml.load(open(args["<input>"]))
    except IOError:
        print "File does not exist."
    np.random.seed(1234)

    T = float(data["temperature"])
    L = float(data["box-size"]) * rc
    n = data["n"]
    eps = kB*T
    tau = sqrt(m0*rc**2/eps)
    m_PMMA = pmma_bead_mass()
    gamma = data["gamma"] * m0/tau
    
    # ===== beads
    pw = float(data["water-vol"])
    if args["--density"] == "real":
        print "Using real density, rho_PMMA = 1180, rho_water = 1000"
        Vw = pw * L**3
        Nc = int(num_chains(rho_PMMA, L, n))     # number of PMMA chains
        Nw = int(rho_water * Vw/(6*18*Maw))
    else:
        print "Using DPD bead density = 3"
        Nw = int(pw * rho_DPD * L**3)
        Nc = int((1-pw) * rho_DPD * L**3/n)
    poly_xyz = grow_polymer(L, n, Nc, mu=rc, sigma=rc/10)
    water_xyz = gen_water_beads(L, Nw, count=Nc+1)
    final_xyz = np.vstack((poly_xyz, water_xyz))
    xyz_str = ll.atoms2str(final_xyz)
    print "Bead density:", len(final_xyz)/(L/rc)**3
    print len(final_xyz), "beads created"

    # ===== bonds
    bonds = create_bonds(n, Nc)
    bonds_str = ll.bonds2str(bonds)
    print len(bonds), "bonds created"

    # ===== pair and bond parameters EDIT
    bead_types = "AW"
    Nbt = len(bead_types)
    r0 = 1.0 * rc
    a_ij = gen_pair_coeffs(bead_types, data["ksi-params"], gamma, rc)
    k_ij = gen_bond_coeffs(bead_types, data["bond-coeffs"], r0)
    masses = {1: m_PMMA*Maw, 2: mw*Maw}

    final_string = ll.header2str(len(final_xyz), len(bonds), Nbt, len(k_ij), L) + \
                   ll.mass2str(masses) + \
                   ll.pair_dpd_coeffs2str(a_ij) + \
                   ll.bond_coeffs2str(k_ij) + \
                   "Atoms\n\n" + xyz_str + \
                   "Bonds\n\n" + bonds_str

    if args["--save"]:
        fname = args["--save"]
        open(fname, "w").write(final_string)
        print "Data file written in", fname
    else:
        print final_string

    if args["--xyz"]:
        fname = args["--xyz"]
        ll.save_xyzfile(fname, final_xyz[:, 1:])
        print "xyz file written in", fname




