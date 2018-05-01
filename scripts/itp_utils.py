import numpy as np

import mbuild as mb


#####################
## These are a collecton of python modules
## to operate with gromacs itp files
#####################


def compound_from_itp(itpfile):
    """ Generate mBuild compound from ITP file 

    Parameters
    ---------
    itpfile : str

    Notes
    -----
    Coordinates are neglected
    """
    itplines = open(itpfile,'r').readlines()
    itplines = remove_comments(itplines)

    molecule_name = parse_molecule_name(itplines)

    cmpd = mb.Compound(name=molecule_name)
    cmpd = parse_atoms(itplines, cmpd)
    cmpd = include_bonds(itplines, cmpd)
    cmpd.name = molecule_name

    return cmpd
    


def remove_comments(itplines):
    """ Remove commented lines and tail comments from itplines """
    newlines = []
    for line in itplines:
        if ';' not in line[0] and line.strip() and '#' not in line[0]:
            newlines.append(line.split(';')[0])

    return newlines

def parse_molecule_name(itplines):
    """ Obtain molecule name """
    moleculetype_directive = find_directive('moleculetype', itplines)
    [molecule_name, nrexcl] = itplines[moleculetype_directive+1].split()

    return molecule_name


def find_directive(directive, itplines):
    """ Find index of directive in itplines """
    for i, line in enumerate(itplines):
        if directive in line and '[' in line and ']' in line:
            return i

    return -1

def parse_atoms(itplines, cmpd):
    """ Return an mBuild compoudn with atoms defined


    Parameters
    ---------
    itplines : 
    cmpd : mb.Compound
    
    Notes
    ------
    nr	type	resnr	residu	atom	cgnr	charge	mass
    """
    atoms_directive = find_directive('atoms', itplines)
    index = atoms_directive

    keep_iterating = True
    while keep_iterating == True:
        index += 1
        atom_info = itplines[index].split()
        if len(atom_info) == 8:
            to_add = mb.Compound(name=atom_info[1], charge=float(atom_info[6]))
            cmpd.add(to_add)
        else:
            keep_iterating = False
    return cmpd

def include_bonds(itplines, cmpd):
    """ Add bonds between atoms """

    bonds_directive = find_directive('bonds', itplines)
    index = bonds_directive

    keep_iterating = True
    while keep_iterating == True:
        index += 1
        bond_info = itplines[index].split()
        if '[' not in bond_info[0] and (len(bond_info) == 3 or len(bond_info) == 5):
            cmpd.add_bond([cmpd.children[ int( bond_info[0] ) - 1 ], 
                           cmpd.children[ int( bond_info[1] ) - 1 ]])
        else:
            keep_iterating = False
    return cmpd

def coordinates_from_compound(source, sink):
    """ Pull coordinates from source into sink
   
    Parameters
    ----------
    source : mb.Compound()
    sink : mb.Compound()

    
    """
    source_particles = [p for p in source.particles()]
    sink_particles = [p for p in sink.particles()]
    assert len(source_particles) == len(sink_particles), \
        "Number particles do not match"
    for i, j in zip(source_particles, sink_particles):
        j.xyz = i.xyz

    return sink

def coordinates_from_file(source, sink):
    """ Pull coordinates from source into sink

    Parameters
    ---------
    source : str
        file of source structure
    sink : mb.Compound()
    """
    return coordinates_from_compound(mb.load(source), sink)

def read_section(directive, itplines):
    """ Extract all the lines from an itp lines under a directive

    Parmaeters
    ----------
    directive : str
        Directive we are looking for 
    itplines : array of str
        ITP file lines

    Returns
    -------
    all_lines : array
        Each line of the itp file under that directive
        """
    all_lines = []
    i = find_directive(directive, itplines)
    keep_iterating = True
    while keep_iterating:
        i += 1
        if len(itplines) > i and itplines[i].strip():
            to_add = itplines[i].strip().split(';')[0]
            if to_add and '[' not in to_add and ']' not in to_add:
                all_lines.append(to_add)
            else:
                keep_iterating = False
        else:
            keep_iterating = False
    return all_lines

def find_directives(itplines):
    """ Iterate through itp file and get all the directives

    Parameters
    ----------
    itplines: array of str

    Returns
    -------
    directives : Dictionary
       keys are directives, values are arrays of corresponding lines 

    Notes
    -----
    If the same directive is listed multiple times, change the name of the
    directive in the dictionary to avoid clashes
        """
    directives = {}
    for line in itplines:
        if '[' in line and ']' in line:
            directive = line.replace('[','')
            directive = directive.replace(']', '')
            directive = directive.strip()
            section = read_section(directive, itplines)
            if directives[directive]:
                directives[directive+"2"] = section
            else:
                directives[directive] = section
    return directives


def find_itp_bond_param(i, j, itp_bond_params):
    """ Find line with the corresponding type

    i,j : strs for each atom
    itp_bond_params : array of itp lines of the angle directive
    """

    for line in itp_bond_params:
        line = line.strip()
        if i.strip() == line.split()[0] and j.strip() == line.split()[1]:
            return line
        elif j.strip() == line.split()[0] and i.strip() == line.split()[1]:
            return line
    return None

def find_itp_angle_param(i, j, k, itp_angle_params):
    """ Find line with the corresponding type

    Parameters
    ---------
    i,j, k : strs for each atom
    itp_angle_params : array of itp lines of the angle directive
    """
    for line in itp_angle_params:
        line = line.strip()
        if j.strip() == line.split()[1]:
            if (i.strip() == line.split()[0] and
                k.strip() == line.split()[2]):
                   return line
            elif (k.strip() == line.split()[0] and
                  j.strip() == line.split()[2]):
                     return line
    return None

def find_itp_dihedral_param(i,j,k,l, itp_dihedral_params, 
                            multiplicity=None):
    """ Find line with the corresponding type
    
    Notes
    -----
    Due to multiplicity, make sure that we're finding
    dihedrals with the same multiplicity

    Parameters
    -----------
    i,j, k, l : strs for each atom
    multiplicity : str, optional
        If not none, then make sure that the multiplicities of the lines agree
        before returning the line
    itp_dihedral_params : array of itp lines of the dihedral directive
    """
    dihedral_lines = []
    for line in itp_dihedral_params:
        line = line.strip()
        if (i.strip() == line.split()[0] and j.strip() == line.split()[1] \
           and k.strip() == line.split()[2] and l.strip() == line.split()[3]) or \
           (l.strip() == line.split()[0] and k.strip() == line.split()[1] \
           and j.strip() == line.split()[2] and i.strip() == line.split()[3]):
                if multiplicity is not None:
                    if line.split()[-1] == multiplicity:
                        #return line
                        dihedral_lines.append(line)
                else:
                    #return line
                    dihedral_lines.append(line)

    if len(dihedral_lines) > 0:
        return dihedral_lines
    else:
        return None


