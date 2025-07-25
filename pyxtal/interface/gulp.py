import os
import re
import shutil
import subprocess

import numpy as np
from ase import Atoms
from ase.units import Ang, eV

from pyxtal import pyxtal
from pyxtal.lattice import Lattice

at_types = {
    "C_c": "C1",  #  =  Sp2 C carbonyl group
    "C_cs": "C2",  # =  Sp2 C in c=S
    "C_c1": "C3",  #  Sp C
    "C_c2": "C4",  # Sp2 C
    "C_c3": "C5",  # =  Sp3 C
    "C_ca": "C6",  # Sp2 C in pure aromatic systems
    "C_cp": "C7",  # Head Sp2 C that connect two rings in biphenyl sys.
    "C_cq": "C8",  # Head Sp2 C that connect two rings in biphenyl sys. identical to cp
    "C_cc": "C9",  # Sp2 carbons in non-pure aromatic systems
    "C_cd": "C10",  # Sp2 carbons in non-pure aromatic systems, identical to cc
    "C_ce": "C11",  # Inner Sp2 carbons in conjugated systems
    "C_cf": "C12",  # Inner Sp2 carbons in conjugated systems, identical to ce
    "C_cg": "C13",  # Inner Sp carbons in conjugated systems
    "C_ch": "C14",  # Inner Sp carbons in conjugated systems, identical to cg
    "C_cx": "C15",  # Sp3 carbons in triangle systems
    "C_cy": "C14",  # Sp3 carbons in square systems
    "C_cu": "C16",  # Sp2 carbons in triangle systems
    "C_cv": "C17",  # Sp2 carbons in square systems
    "C_cz": "C18",  # Sp2 carbon in guanidine group
    "H_h1": "H1",  # H bonded to aliphatic carbon with 1 electrwd. group
    "H_h2": "H2",  # H bonded to aliphatic carbon with 2 electrwd. group
    "H_h3": "H3",  # H bonded to aliphatic carbon with 3 electrwd. group
    "H_h4": "H4",  # H bonded to non-sp3 carbon with 1 electrwd. group
    "H_h5": "H5",  # H bonded to non-sp3 carbon with 2 electrwd. group
    "H_ha": "H6",  # H bonded to aromatic carbon
    "H_hc": "H7",  # H bonded to aliphatic carbon without electrwd. group
    "H_hn": "H8",  # H bonded to nitrogen atoms
    "H_ho": "H9",  # Hydroxyl group
    "H_hp": "H10",  # H bonded to phosphate
    "H_hs": "H11",  # Hydrogen bonded to sulphur
    "H_hw": "H12",  # Hydrogen in water
    "H_hx": "H13",  # H bonded to C next to positively charged group
    "F": "F",  # Fluorine
    "Cl": "Cl",  # Chlorine
    "Br": "Br",  # Bromine
    "I": "I",  #  Iodine
    "N_n": "N1",  # Sp2 nitrogen in amide groups
    "N_n1": "N2",  # Sp N
    "N_n2": "N3",  # aliphatic Sp2 N with two connected atoms
    "N_n3": "N4",  # Sp3 N with three connected atoms
    "N_n4": "N5",  # Sp3 N with four connected atoms
    "N_na": "N6",  # Sp2 N with three connected atoms
    "N_nb": "N7",  # Sp2 N in pure aromatic systems
    "N_nc": "N8",  # Sp2 N in non-pure aromatic systems
    "N_nd": "N9",  # Sp2 N in non-pure aromatic systems, identical to nc
    "N_ne": "N10",  # Inner Sp2 N in conjugated systems
    "N_nf": "N11",  # Inner Sp2 N in conjugated systems, identical to ne
    "N_nh": "N12",  # Amine N connected one or more aromatic rings
    "N_no": "N13",  # Nitro N
    "N_ns": "N14",  # amind N, with 1 attached hydrogen atom
    "N_nt": "N15",  # amide N, with 2 attached hydrogen atoms
    "N_nx": "N16",  # like n4, but only has one hydrogen atom
    "N_ny": "N17",  # like n4, but only has two hydrogen atoms
    "N_nz": "N18",  # like n4, but only has three three hydrogen atoms
    "N_n+": "N19",  # NH4+
    "N_nu": "N20",  # like nh, but only has one attached hydrogen atom
    "N_nv": "N21",  # like nh, but only has two attached hydrogen atoms
    "N_n7": "N22",  # like n3, but only has one attached hydrogen atom
    "N_n8": "N23",  # like n3, but only has two attached hydrogen atoms
    "N_n9": "N24",  # NH3
    "O_o": "O1",  # Oxygen with one connected atom
    "O_oh": "O2",  # Oxygen in hydroxyl group
    "O_os": "O3",  # Ether and ester oxygen
    "O_ow": "O4",  # Oxygen in water
    "P_p2": "P1",  # Phosphate with two connected atoms
    "P_p3": "P2",  # Phosphate with three connected atoms, such as PH3
    "P_p4": "P3",  # Phosphate with three connected atoms, such as O=P(CH3)2
    "P_p5": "P4",  # Phosphate with four connected atoms, such as O=P(OH)3
    "P_pb": "P5",  # Sp2 P in pure aromatic systems
    "P_pc": "P6",  # Sp2 P in non-pure aromatic systems
    "P_pd": "P7",  # Sp2 P in non-pure aromatic systems, identical to pc
    "P_pe": "P8",  # Inner Sp2 P in conjugated systems
    "P_pf": "P9",  # Inner Sp2 P in conjugated systems, identical to pe
    "P_px": "P10",  # Special p4 in conjugated systems
    "P_py": "P11",  # Special p5 in conjugated systems
    "S_s": "S1",  # S with one connected atom
    "S_s2": "S2",  # S with two connected atom, involved at least one double bond
    "S_s4": "S3",  # S with three connected atoms
    "S_s6": "S4",  # S with four connected atoms
    "S_sh": "S5",  # Sp3 S connected with hydrogen
    "S_ss": "S6",  # Sp3 S in thio-ester and thio-ether
    "S_sx": "S7",  # Special s4 in conjugated systems
    "S_sy": "S8",  # Special s6 in conjugated systems
}


class GULP:
    """
    A calculator to perform atomic structure optimization in GULP

    Args:

    struc: structure object generated by Pyxtal
    ff: path of forcefield lib
    opt: `conv`, `conp`, `single`
    pstress (float): external pressure
    steps (int): relaxation steps
    symm (bool): whether or not impose the symmetry
    """

    def __init__(
        self,
        struc,
        label="_",
        path="tmp",
        ff="reaxff",
        pstress=None,
        opt="conp",
        steps=1000,
        exe="gulp",
        input="gulp.in",
        output="gulp.log",
        dump=None,
        symmetry=False,
        labels=None,
        timeout=3600,
    ):
        if isinstance(struc, pyxtal):
            self.pyxtal = struc
            self.species = struc.species
            struc = struc.to_ase(resort=False)
        else:
            self.pyxtal = None

        if isinstance(struc, Atoms):
            self.lattice = Lattice.from_matrix(struc.cell)
            self.frac_coords = struc.get_scaled_positions()
            self.sites = struc.get_chemical_symbols()
            self.species = None
        else:
            raise NotImplementedError("only support ASE atoms object")

        self.symmetry = symmetry  # ; print(self.pyxtal.lattice.ltype)
        self.structure = struc
        self.pstress = pstress
        self.label = label
        self.labels = labels
        self.ff = ff
        self.opt = opt
        self.exe = exe
        self.steps = steps
        self.folder = path
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        self.input  = self.label + input
        self.output = self.label + output
        self.dump = dump
        self.iter = 0
        self.energy = None
        self.energy_per_atom = None
        self.stress = None
        self.forces = None
        self.positions = None
        self.optimized = False
        self.cputime = 0
        self.error = False
        self.timeout = timeout

    def set_catlow(self):
        """
        set the atomic label for catlow potentials
        O_O2- general O2- species
        O_OH oxygen in hydroxyl group
        H_OH hydrogen in hydroxyl group
        """

    def run(self, clean=True):
        """
        Always go to the directory to run one gulp at once
        """
        cwd = os.getcwd()
        os.chdir(self.folder)
        self.write()
        self.execute()
        self.read()
        if clean:
            self.clean()
        os.chdir(cwd)

    def execute(self):
        cmd = self.exe + "<" + self.input + ">" + self.output
        # os.system(cmd)
        with open(os.devnull, 'w') as devnull:
            try:
                # Run the external command with a timeout
                result = subprocess.run(
                    cmd, shell=True, timeout=self.timeout, check=True, stderr=devnull)
                return result.returncode  # Or handle the result as needed
            except subprocess.CalledProcessError as e:
                print(f"Command '{cmd}' failed with return code {e.returncode}.")
                return None
            except subprocess.TimeoutExpired:
                print(f"External command {cmd} timed out.")
                return None

    def clean(self):
        if self.error:
            os.system("mv " + self.input + " " + self.input + "_error")
            os.system("mv " + self.output + " " + self.output + "_error")
        else:
            os.remove(self.input)
            os.remove(self.output)
        if self.dump is not None:
            os.remove(self.dump)

    def to_ase(self):
        return Atoms(self.sites, scaled_positions=self.frac_coords, cell=self.lattice.matrix)

    def to_pymatgen(self):
        from pymatgen.core.structure import Structure

        return Structure(self.lattice.matrix, self.sites, self.frac_coords)

    def to_pyxtal(self):
        ase_atoms = self.to_ase()
        for tol in [1e-2, 1e-3, 1e-4, 1e-5]:
            try:
                struc = pyxtal()
                struc.from_seed(ase_atoms, tol=tol)
                break
            except:
                pass
                # print('Something is wrong', tol)
                # struc.from_seed('bug.vasp', tol*10)
        return struc

    def write(self):
        a, b, c, alpha, beta, gamma = self.lattice.get_para(degree=True)

        with open(self.input, "w") as f:
            if self.opt == "conv":
                f.write(f"opti stress {self.opt:s} conjugate ")
            elif self.opt == "single":
                f.write("grad conp stress ")
            else:
                f.write(f"opti stress {self.opt:s} conjugate ")

            if not self.symmetry:
                f.write("nosymmetry\n")

            f.write("\ncell\n")
            f.write(f"{a:12.6f}{b:12.6f}{c:12.6f}{alpha:12.6f}{beta:12.6f}{gamma:12.6f}\n")
            f.write("\nfractional\n")

            if self.symmetry and self.pyxtal is not None:
                # Use pyxtal here
                for site in self.pyxtal.atom_sites:
                    symbol, coord = site.specie, site.position
                    f.write("{:4s} {:12.6f} {:12.6f} {:12.6f} core \n".format(symbol, *coord))
                    if self.ff == "catlow" and symbol == "O":
                        f.write("{:4s} {:12.6f} {:12.6f} {:12.6f} shell \n".format(symbol, *coord))

                # Tested for all space groups
                f.write(f"\nspace\n{self.pyxtal.group.number:d}\n")
                f.write("\norigin\n0 0 0\n")
            else:
                # All coordinates
                for coord, site in zip(self.frac_coords, self.sites):
                    f.write("{:4s} {:12.6f} {:12.6f} {:12.6f} core \n".format(site, *coord))
            species = self.structure.species if self.species is not None else list(set(self.sites))

            f.write("\nSpecies\n")
            if self.labels is not None:
                for specie in species:
                    if specie in self.labels:
                        sp = self.labels[specie]
                        f.write(f"{specie:4s} core {sp:s}\n")
                    else:
                        f.write(f"{specie:4s} core {specie:4s}\n")
            else:
                for specie in species:
                    if self.ff == "catlow" and specie == "O":
                        f.write("O    core O_O2- core\n")
                        f.write("O    shell O_O2- shell\n")
                    else:
                        f.write(f"{specie:4s} core {specie:4s}\n")

            f.write(f"\nlibrary {self.ff:s}\n")
            f.write("ewald 10.0\n")
            # f.write('switch rfo gnorm 1.0\n')
            # f.write('switch rfo cycle 0.03\n')
            if self.opt != "single":
                f.write(f"maxcycle {self.steps:d}\n")
            if self.pstress is not None:
                f.write(f"pressure {self.pstress:6.3f}\n")
            if self.dump is not None:
                f.write(f"output cif {self.dump:s}\n")

    def read(self):
        # for symmetry case
        lattice_para = None
        lattice_vector = None
        ltype = self.pyxtal.lattice.ltype if self.pyxtal is not None else "triclinic"

        with open(self.output) as f:
            lines = f.readlines()
        try:
            for i, line in enumerate(lines):
                if self.symmetry and self.pyxtal.group.symbol[0] != "P":
                    m = re.match(r"\s*Non-primitive unit cell\s*=\s*(\S+)\s*eV", line)
                elif self.pstress is None or self.pstress == 0:
                    m = re.match(r"\s*Total lattice energy\s*=\s*(\S+)\s*eV", line)
                else:
                    m = re.match(r"\s*Total lattice enthalpy\s*=\s*(\S+)\s*eV", line)
                # print(line.find('Final asymmetric unit coord'), line)
                if m:
                    self.energy = float(m.group(1))
                    self.energy_per_atom = self.energy / len(self.frac_coords)

                elif line.find("Job Finished") != -1:
                    self.optimized = True

                elif line.find("Total CPU time") != -1:
                    self.cputime = float(line.split()[-1])

                elif line.find("Final stress tensor components") != -1:
                    stress = np.zeros([6])
                    for j in range(3):
                        var = lines[i + j + 3].split()[1]
                        stress[j] = float(var)
                        var = lines[i + j + 3].split()[3]
                        stress[j + 3] = float(var)
                    self.stress = stress

                # Forces, QZ copied from https://gitlab.com/ase/ase/-/blob/master/ase/calculators/gulp.py
                elif line.find("Final internal derivatives") != -1:
                    s = i + 5
                    forces = []
                    while True:
                        s = s + 1
                        if lines[s].find("------------") != -1:
                            break
                        g = lines[s].split()[3:6]

                        for _t in range(3 - len(g)):
                            g.append(" ")
                        for j in range(2):
                            min_index = [i + 1 for i, e in enumerate(g[j][1:]) if e == "-"]
                            if j == 0 and len(min_index) != 0:
                                if len(min_index) == 1:
                                    g[2] = g[1]
                                    g[1] = g[0][min_index[0] :]
                                    g[0] = g[0][: min_index[0]]
                                else:
                                    g[2] = g[0][min_index[1] :]
                                    g[1] = g[0][min_index[0] : min_index[1]]
                                    g[0] = g[0][: min_index[0]]
                                    break
                            if j == 1 and len(min_index) != 0:
                                g[2] = g[1][min_index[0] :]
                                g[1] = g[1][: min_index[0]]

                        G = [-float(x) * eV / Ang for x in g]
                        forces.append(G)
                    forces = np.array(forces)
                    self.forces = forces

                elif line.find(" Cycle: ") != -1:
                    self.iter = int(line.split()[1])

                # asymmetric unit
                elif line.find("Final asymmetric unit coordinates") != -1:
                    s = i + 6
                    positions = []
                    for _i in range(len(self.pyxtal.atom_sites)):
                        xyz = lines[s + _i].split()[3:6]
                        XYZ = [float(x) for x in xyz]
                        # print(XYZ)
                        self.pyxtal.atom_sites[_i].update(XYZ)

                elif line.find("Final fractional coordinates of atoms") != -1:
                    s = i + 5
                    positions = []
                    species = []
                    while True:
                        s = s + 1
                        if lines[s].find("------------") != -1:
                            break
                        xyz = lines[s].split()[3:6]
                        XYZ = [float(x) for x in xyz]
                        positions.append(XYZ)
                        species.append(lines[s].split()[1])
                    # if len(species) != len(self.sites):
                    #    print("Warning", len(species), len(self.sites))
                    self.frac_coords = np.array(positions)
                elif line.find("Final Cartesian lattice vectors") != -1:
                    lattice_vectors = np.zeros((3, 3))
                    s = i + 2
                    for j in range(s, s + 3):
                        temp = lines[j].split()
                        for k in range(3):
                            lattice_vectors[j - s][k] = float(temp[k])
                    lattice_vector = Lattice.from_matrix(lattice_vectors, ltype=ltype)

                elif line.find("Non-primitive lattice parameters") != -1:
                    s = i + 2
                    temp = lines[s].split()
                    a, b, c = float(temp[2]), float(temp[5]), float(temp[8])
                    temp = lines[s + 1].split()
                    alpha, beta, gamma = float(temp[1]), float(temp[3]), float(temp[5])
                    lattice_para = Lattice.from_para(a, b, c, alpha, beta, gamma, ltype)
        except:
            self.error = True
            self.energy = None
        if lattice_para is not None:
            self.lattice = lattice_para
        elif lattice_vector is not None:
            self.lattice = lattice_vector
        else:
            self.error = True
            self.energy = None

        if self.pyxtal is not None:
            self.pyxtal.lattice = self.lattice

        if self.energy is None or np.isnan(self.energy):
            self.error = True
            self.energy = None
            print("GULP calculation is wrong, reading------")


class GULP_OC:
    """
    A calculator to perform oragnic crystal structure optimization in GULP

    Args:
        struc: structure object generated by Pyxtal
        ff: path of forcefield lib, e.g., `gaff`
        bond_type: specify the bond type or not (GULP can detect it automatically)
        opt: e.g., `conv`, `conp`, `single`
        steps: number of steps, int, e.g., `1000`
        exe: int, the way to call gulp executable
        atom_info: atomic labels/charges
        input: gulp input file name
        output: gulp output file name
        dump: dumped gulp file name
    """

    def __init__(
        self,
        struc,
        label="_",
        ff="gaff2",
        bond_type=False,
        opt="conp",
        steps=1000,
        stepmx=0.001,
        exe="gulp",
        atom_info=None,
        input="gulp.in",
        output="gulp.log",
        dump=None,
        folder=".",
    ):
        self.folder = folder
        self.structure = struc
        self.label = label
        self.ff = ff
        self.bond_type = bond_type
        self.opt = opt
        self.exe = exe
        if "OCSP_GULPEXE" in os.environ:
            self.exe = os.environ["OCSP_GULPEXE"]
        self.steps = steps
        self.stepmx = stepmx
        self.opt = opt
        self.input = self.label + input
        self.output = self.label + output
        self.dump = dump
        self.iter = 0
        self.stress = None
        self.positions = None
        self.forces = None
        self.optimized = False
        self.cell = None
        self.group = self.structure.group
        self.optlat = False
        self.cputime = 0
        self.atom_info = atom_info

    def run(self, clean=True, pause=False):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        cwd = os.getcwd()
        os.chdir(self.folder)

        self.write()
        if not pause:
            self.execute()
            self.read()
            if clean:
                self.clean()

        os.chdir(cwd)

    def execute(self):
        if self.exe == "gulp.exe":
            key = self.input.split(".")[0]
            shutil.copy(self.input, key + ".gin")
            cmd = self.exe + " " + key
            os.system(cmd)
            shutil.copy(key + ".gout", self.output)
        else:
            cmd = self.exe + "<" + self.input + ">" + self.output
            os.system(cmd)

    def clean(self):
        os.remove(self.input)
        os.remove(self.output)

    def write(self):
        lat = self.structure.lattice
        a, b, c = lat.a, lat.b, lat.c
        alpha, beta, gamma = (
            np.degrees(lat.alpha),
            np.degrees(lat.beta),
            np.degrees(lat.gamma),
        )
        ltype = lat.ltype

        with open(self.input, "w") as f:
            # f.write('opti stress {:s} conj molecule nomod qok\n'.format(self.opt))
            if self.opt == "conv":
                # f.write('opti {:s} steepest molecule nomod qok\n'.format(self.opt))
                f.write(f"opti {self.opt:s} conj molecule nomod qok\n")
            else:
                f.write(f"opti stress {self.opt:s} conj molecule nomod qok\n")
            f.write("\ncell\n")
            f.write(f"{a:12.6f}{b:12.6f}{c:12.6f}{alpha:12.6f}{beta:12.6f}{gamma:12.6f}\n")
            f.write("\nfractional\n")

            symbols = []

            for i, site in enumerate(self.structure.mol_sites):
                coords, species = site._get_coords_and_species(first=True)
                if self.atom_info is None:
                    labels = site.molecule.props["gmx_label"]
                    charges = site.molecule.props["charge"]
                else:
                    labels = self.atom_info["label"][site.type]
                    charges = self.atom_info["charge"][site.type]
                for j, coord in enumerate(coords):
                    # print(len(site.molecule.mol.sites), len(labels), len(coords), coord)
                    symbol = site.molecule.mol.sites[j].species_string
                    if symbol not in ["F", "Cl", "Br"]:
                        symbol += "_" + labels[j]
                    symbols.append(symbol)
                    try:
                        f.write(
                            f"{at_types[symbol]:4s} {coord[0]:12.6f} {coord[1]:12.6f} {coord[2]:12.6f} core {charges[j]:12.6f}\n"
                        )
                    except KeyError:
                        msg = f"symbol {symbol:s} is not supported in GULP-gaff2.lib"
                        raise KeyError(msg)

            f.write("\nSpecies\n")
            symbols = list(set(symbols))
            for symbol in symbols:
                f.write(f"{at_types[symbol]:4s} core {symbol:4s}\n")

            # symmetry operations
            f.write(f"\nsymmetry_cell {ltype:s}\n")
            site0 = self.structure.mol_sites[0]
            for op in site0.wp.ops[1:]:
                f.write("symmetry_operator\n")
                rot = op.rotation_matrix.T
                trans = op.translation_vector
                for i in range(3):
                    f.write("{:6.3f} {:6.3f} {:6.3f} {:6.3f}\n".format(*rot[i, :], trans[i]))

            # bond type
            if self.bond_type:
                for bond in site0.mol.molTopol.bonds:
                    for i in range(len(site.wp)):
                        count = i * len(coords)
                        f.write(f"connect {bond.atoms[0].id + count:4d} {bond.atoms[1].id + count:4d}\n")
            f.write(f"\nlibrary {self.ff:s}.lib\n")
            # f.write('\nlibrary {:s}\n'.format(self.ff))
            if "OCSP_GULP_LIB" in os.environ:
                shutil.copy(os.environ["OCSP_GULP_LIB"] + "/" + self.ff + ".lib", ".")
            f.write("ewald 10.0\n")
            # f.write('switch rfo gnorm 1.0\n')
            # f.write('switch lbfgs cycle 300\n')
            f.write(f"maxcycle {self.steps:d}\n")
            f.write("stepmx " + str(self.stepmx) + "\n")
            f.write("ftol 0.0001\n")  # energy tol default: 1e-5
            f.write("gtol 0.002\n")  # force tol default: 1e-4
            f.write("gmax 0.01\n")  # force tol defult: 1e-3
            if self.dump is not None:
                f.write(f"output cif {self.dump:s}\n")
            # https://gulp.curtin.edu.au/gulp/help/new_help_40_txt.html#gmax

    def read(self):
        with open(self.output) as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if i == 7:
                self.version = line

            if line.find("Total lattice energy") >= 0:
                m = re.match(r"\s*Total lattice energy\s*=\s*(\S+)\s*eV", line)
                if m:
                    self.structure.energy = float(m.group(1))
            else:
                if line.find("Job Finished") != -1:
                    self.optimized = True

                elif line.find("Total CPU time") != -1:
                    self.cputime = float(line.split()[-1])

                elif line.find("Final stress tensor components") != -1:
                    stress = np.zeros([6])
                    for j in range(3):
                        var = lines[i + j + 3].split()[1]
                        stress[j] = float(var)
                        var = lines[i + j + 3].split()[3]
                        stress[j + 3] = float(var)
                    self.stress = stress

                elif line.find(" Cycle: ") != -1:
                    self.iter = int(line.split()[1])

                elif (
                    line.find("Final asymmetric unit coord") != -1
                    or line.find("Final fractional coordinates of atoms") != -1
                ):
                    s = i + 5
                    positions = []
                    species = []
                    while True:
                        s = s + 1
                        if lines[s].find("------------") != -1:
                            break
                        # if lines[s].find(" s ") != -1:
                        #    continue
                        xyz = lines[s].split()[3:6]
                        XYZ = [float(x) for x in xyz]
                        positions.append(XYZ)
                        species.append(lines[s].split()[1])
                    self.positions = np.array(positions)
                    self.species = species

                elif line.find("Final Cartesian lattice vectors") != -1:
                    lattice_vectors = np.zeros((3, 3))
                    s = i + 2
                    for j in range(s, s + 3):
                        temp = lines[j].split()
                        for k in range(3):
                            lattice_vectors[j - s][k] = float(temp[k])
                    self.cell = lattice_vectors
        if self.cell is None:
            self.cell = self.structure.lattice.matrix

        self.lattice = Lattice.from_matrix(self.cell)  # update the lattice
        self.lattice.ltype = self.structure.group.lattice_type
        self.structure.lattice = self.lattice

        if self.optimized:
            count = 0

            try:
                for site in self.structure.mol_sites:
                    coords = self.positions[count : count + len(site.molecule.mol)]
                    site.update(coords, self.lattice)
                    count += len(site.molecule.mol)
                self.structure.optimize_lattice()
            except:
                # print()
                print("Structure is wrong after optimization")


def single_optimize(
    struc,
    ff,
    steps=1000,
    pstress=None,
    opt="conp",
    path="tmp",
    label="_",
    clean=True,
    symmetry=False,
    labels=None,
):
    calc = GULP(
        struc,
        steps=steps,
        label=label,
        path=path,
        pstress=pstress,
        ff=ff,
        opt=opt,
        symmetry=symmetry,
        labels=labels,
    )

    calc.run(clean=clean)

    if calc.error:
        print("GULP error in single optimize")
        return None, None, 0, True
    else:
        struc = calc.to_pyxtal() if calc.pyxtal is None else calc.pyxtal
        # if sum(struc.numIons) == 42: print("SSSSS"); import sys; sys.exit()
        return struc, calc.energy_per_atom, calc.cputime, calc.error


def optimize(
    struc,
    ff,
    optimizations=None,
    exe="gulp",
    pstress=None,
    path="tmp",
    label="_",
    clean=True,
    adjust=False,
):
    """
    Multiple calls

    """
    if optimizations is None:
        optimizations = ["conp", "conp"]
    time_total = 0
    for opt in optimizations:
        struc, energy, time, error = single_optimize(
            struc,
            ff,
            pstress=pstress,
            opt=opt,
            exe=exe,
            path=path,
            label=label,
            clean=clean,
        )

        time_total += time
        if error:
            return None, None, 0, True
        elif adjust and abs(energy) < 1e-8:
            matrix = struc.lattice.matrix
            struc.lattice.set_matrix(matrix * 0.8)

    return struc, energy, time_total, False


if __name__ == "__main__":
    while True:
        struc = pyxtal()
        struc.from_random(3, 19, ["C"], [4])
        if struc.valid:
            break
    print(struc)
    pmg1 = struc.to_pymatgen()
    calc = GULP(struc, opt="single", ff="tersoff.lib")
    calc.run(clean=False)  # ; import sys; sys.exit()
    print(calc.energy)
    print(calc.stress)
    print(calc.forces)
    pmg2 = calc.to_pymatgen()
    # xtal = calc.pyxtal #calc.to_pyxtal()
    # print(calc.iter)
    # print(xtal)

    import pymatgen.analysis.structure_matcher as sm

    print(sm.StructureMatcher().fit(pmg1, pmg2))

    struc, eng, time, _ = optimize(struc, ff="tersoff.lib")
    print(struc)
    print(eng)
    print(time)
