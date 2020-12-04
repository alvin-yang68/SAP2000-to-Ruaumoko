# -*- coding: utf-8 -*-
"""
nodes.py: The s2k joints to rmk nodes convert module, which defines the 
functions required to perform conversion, as well as other utilities. The class 
definitions for StoreyNodes is also defined in this module.
"""

import config as cfg
from config import data_retriever
import lumped_weights

def convert(s2k_data):
    """
    Converts the s2k joint coordinates to rmk nodal definitions. This is the 
    main function of this module which executes the other functions.
    """
    nodes_instances = {}        # {unique height : a StoreyNodes instance}
    
    raw_strct_ndl_pnt  = {}     # {s2k joint ID : storey rmk_ndl_pnt}
    stry_data = {}              # {rmk node no. : {x-coord, y-coord, z-coord}}
    
    # Organize the joint restraints for use later
    s2k_jnt_rstrt = data_retriever(s2k_data, cfg.title_joint_restraint)
    jnts_to_rstrt = {line[cfg.jnt_rstrt] : line for line in s2k_jnt_rstrt}
    
    # Organize the joint coordinates for use later
    s2k_jnt_coords = data_retriever(s2k_data, cfg.title_joint_coordinates)
    
        # {joint vertical position : corresponding s2k_jnt_coords line}
    rfd_jnt ={}
    
    for line in s2k_jnt_coords:
        # Group the joints in terms of their vertical position
        rfd_jnt = entry_cnstrt_sorter(rfd_jnt, line[cfg.z], line)
           
        # Obtain the unique heights of every joints
    unq_heights = list(rfd_jnt.keys())
    unq_heights.sort()
    
    # Set the node no. and node coords
    for height in unq_heights:
        # Create an instance of StoreyNodes to service each unique height
        nodes_instances.update({height : StoreyNodes(height)})
        raw_strct_ndl_pnt, stry_data = nodes_instances[height].set_nd_coords(
                raw_strct_ndl_pnt, stry_data, rfd_jnt[height], jnts_to_rstrt, 
                (2*len(unq_heights)-2))
    
    # Apply rigid diaphragm effect and body constraints
    raw_strct_ndl_pnt, weight_instances = constrainer(
            s2k_data,raw_strct_ndl_pnt, stry_data)
    
    # Create a printable outputs in rmk format for raw_strct_ndl_pnt
    rmk_ndl_pnt_txt = txt_format(raw_strct_ndl_pnt)
    
    return rmk_ndl_pnt_txt, nodes_instances, weight_instances

def constrainer(s2k_data, raw_strct_ndl_pnt, stry_data):
    """ This function produces the constraint data (body constraint and rigid 
    diaphragm constrain) for all the nodes in raw_strct_ndl_pnt. It then updates 
    the boundary_cnstrt code for all DoFs and master node no. of raw_strct_ndl_pnt. """
    # Organize the joint to be constrained and constraint definitions  for use later
    s2k_jnt_cnstrt = data_retriever(s2k_data, cfg.title_joint_constraint)
    s2k_cnstrt_def = data_retriever(s2k_data, cfg.title_constraint_definitions)
    
        # {constraint title : [[joints to constraint], {constraint data}]}
    rfd_body = {}
        # {constraint title : [joints to constraint]}
    rfd_diaph = {}
    
    for line in s2k_jnt_cnstrt:  
        # Separate values for rfd_body and rfd_diaph from s2k_jnt_cnstrt
        if line[cfg.typ] == cfg.body:
            rfd_body = entry_cnstrt_sorter(rfd_body, line[cfg.cnstrt], 
                                    line[cfg.jnt_cnstrt])
        elif line[cfg.typ] == cfg.diaph:
            rfd_diaph = entry_cnstrt_sorter(rfd_diaph, line[cfg.cnstrt], 
                                     line[cfg.jnt_cnstrt])
    
    for line in s2k_cnstrt_def:
        # Append the constraint data from s2k_cnstrt_def to rfd_body
        try:
            rfd_body[line[cfg.name]].append(line)
        except KeyError:
            continue
    
        # Get the centre of mass and assign it as the master node of the 
        # diaphragm constraint
    weight_instances, raw_strct_ndl_pnt, get_com = lumped_weights.get_com(
            s2k_data, rfd_diaph, stry_data, raw_strct_ndl_pnt)
    
    # Apply the rigid diaphragm constraints and update the raw_strct_ndl_pnt 
    for diaph_id, group in rfd_diaph.items():
        # Iterate through rfd_diaph.values()
        mstr_nd = get_com[diaph_id]
        
        for jnt_id in group:
            # Set rigid diaphragm
            raw_strct_ndl_pnt[jnt_id]['N1'] = 2
            raw_strct_ndl_pnt[jnt_id]['N3'] = 2
            raw_strct_ndl_pnt[jnt_id]['N5'] = 2
            raw_strct_ndl_pnt[jnt_id]['KUP1'] = mstr_nd
    
    # Apply the body constraints and update the raw_strct_ndl_pnt 
    for group in rfd_body.values():
        # Iterate through rfd_body.values()
        ordered_nodes = list(map(int,group[0:-1]))
        ordered_nodes.sort()
        ordered_nodes = list(map(str,ordered_nodes))
        mstr_nd = ordered_nodes[0]      # Master node is the first entry_cnstrt (random)
                                # of the rfd_body.values() list
        cnstrt_def = group[-1]
        
        for jnt_id in ordered_nodes[1:]:
            # Constraint the DoFs of a node based on the s2k definition
            master_1 = []
            if cnstrt_def[cfg.ux_cnstrt] == cfg.yes:
                raw_strct_ndl_pnt[jnt_id]['N1'] = 3
            
            master_1.append(raw_strct_ndl_pnt[jnt_id]['N1'])
                
            if cnstrt_def[cfg.uz_cnstrt] == cfg.yes:
                raw_strct_ndl_pnt[jnt_id]['N2'] = 3
            
            master_1.append(raw_strct_ndl_pnt[jnt_id]['N2'])
            
            if cnstrt_def[cfg.uy_cnstrt] == cfg.yes:
                raw_strct_ndl_pnt[jnt_id]['N3'] = 3
                # NOTE: Ruaumoko swaps the y-axis and z-axis
            
            master_1.append(raw_strct_ndl_pnt[jnt_id]['N3'])
            
            if cnstrt_def[cfg.rx_cnstrt] == cfg.yes:
                raw_strct_ndl_pnt[jnt_id]['N4'] = 3
            
            master_1.append(raw_strct_ndl_pnt[jnt_id]['N4'])
            
            if cnstrt_def[cfg.rz_cnstrt] == cfg.yes:
                raw_strct_ndl_pnt[jnt_id]['N5'] = 3
            
            master_1.append(raw_strct_ndl_pnt[jnt_id]['N5'])
            
            if cnstrt_def[cfg.ry_cnstrt] == cfg.yes:
                raw_strct_ndl_pnt[jnt_id]['N6'] = 3
                # NOTE: Ruaumoko swaps the y-axis and z-axis
            
            master_1.append(raw_strct_ndl_pnt[jnt_id]['N6'])
            
            if 2 not in master_1:
                # If all the DoFs are slaved to a node, then change the 3 to 2
                if raw_strct_ndl_pnt[jnt_id]['N1'] == 3:
                    raw_strct_ndl_pnt[jnt_id]['N1'] -= 1
                
                if raw_strct_ndl_pnt[jnt_id]['N2'] == 3:
                    raw_strct_ndl_pnt[jnt_id]['N2'] -= 1
                
                if raw_strct_ndl_pnt[jnt_id]['N3'] == 3:
                    raw_strct_ndl_pnt[jnt_id]['N3'] -= 1
                
                if raw_strct_ndl_pnt[jnt_id]['N4'] == 3:
                    raw_strct_ndl_pnt[jnt_id]['N4'] -= 1
                
                if raw_strct_ndl_pnt[jnt_id]['N5'] == 3:
                    raw_strct_ndl_pnt[jnt_id]['N5'] -= 1
                
                if raw_strct_ndl_pnt[jnt_id]['N6'] == 3:
                    raw_strct_ndl_pnt[jnt_id]['N6'] -= 1
                
                raw_strct_ndl_pnt[jnt_id]['KUP1'] = (
                        raw_strct_ndl_pnt[mstr_nd]['N'])
            else:
                raw_strct_ndl_pnt[jnt_id]['KUP2'] = (
                        raw_strct_ndl_pnt[mstr_nd]['N'])
    
    return raw_strct_ndl_pnt, weight_instances

def txt_format(raw_strct_ndl_pnt):
    """ This function creates a printable format that can be exported to a 
    txt file """
    rmk_ndl_pnt_txt = ''
    
    for line in raw_strct_ndl_pnt.values():
        txt_1 = '{0}\t{1}\t{2}\t{3}\t{4}\t'.format(
                line['N'], line['X'], line['Y'], line['Z'], line['N1'])
        txt_2 = '{0}\t{1}\t{2}\t{3}\t'.format(
                line['N2'], line['N3'], line['N4'], line['N5'])
        txt_3 = '{0}\t{1}\t{2}\t{3}\n'.format(
                line['N6'], line['KUP1'], line['IOUT'], line['KUP2'])
        
        rmk_ndl_pnt_txt += txt_1 + txt_2 + txt_3
    
    return rmk_ndl_pnt_txt

def entry_cnstrt_sorter(target_dict, line_key, line_val):
    """
    This function is used to group the entries (line_val) or a section of the 
    dictionary_cnstrt (target_dict) in terms of the entry_cnstrt of a column (line_key).
    """
    if line_key in target_dict.keys():
        target_dict[line_key].append(line_val)
    else:
        target_dict.update({line_key : [line_val]})
        
    return target_dict

def get_dictionaries(nodes_instances):
    """ This function returns the dictionaries: prop_to_mmbr, s2k_to_rmk_frm, 
    and s2k_to_rmk_link """
    s2k_to_rmk_nd = {}
    
    for stry_nds_inst in nodes_instances.values():
        s2k_to_rmk_nd.update(stry_nds_inst.s2k_to_rmk_nd)
        
    return s2k_to_rmk_nd

class StoreyNodes:
    """
    A StoreyNodes instance contains all the nodal coords of a storey of the 
    structure. The function set_nd_coords is used to convert nodal point 
    coordinates from s2k to rmk format.
    """
    def __init__(self, height):
        """ Initializer with a 'height' and storey nodal point parameter to 
        inform the storey height of these instances. """
        self.height = height
        
        self.stry_data = {}         # {rmk node no. : {x-coord, y-coord, z-coord}}
        self.s2k_to_rmk_nd = {}     # {s2k joint ID : rmk node no.}
        
    def __str__(self):
        """ For print() and str() """
        return 'This instance has a height of: {}'.format(self.height)
    
    def __repr__(self):
        """ For repr() and interactive prompt """
        return 'StoreyNodes(height={})'.format(self.height)
    
    def set_nd_coords(self, raw_strct_ndl_pnt, stry_data, stry_rfd_jnt, 
                      jnts_to_rstrt, storey_no):
        """ Set the node no., node coordinates, and restraints data. Then update 
        the s2k joint ID to rmk node no. dictionary_cnstrt (s2k_to_rmk_nd) and storey 
        data (stry_data). """
        for line in stry_rfd_jnt:
            nd_no = len(raw_strct_ndl_pnt) + storey_no + 2
            
            jnt_id = line[cfg.jnt_coords]
            x = round(float(line[cfg.x]), 4)
            y = round(float(line[cfg.z]), 4)
            z = round(float(line[cfg.y]), 4)
                # NOTE: Ruaumoko swaps the y-axis and z-axis
            
            # Update variables used by other modules
            self.s2k_to_rmk_nd.update({jnt_id : nd_no})
            self.stry_data.update({nd_no : {'X':x, 'Y':y, 'Z':z}})
            
            # Please edit the following lines should Ruaumoko format changes
            rmk_line_ndl_pnt = {'N':nd_no, 'X':x, 'Y':y, 'Z':z}
            
            rmk_line_ndl_pnt.update({'N1':0, 'N2':0, 'N3':0, 'N4':0, 'N5':0, 
                                     'N6':0, 'KUP1':0, 'IOUT':0, 'KUP2':0})
            
            if jnt_id in jnts_to_rstrt.keys():
                # Check if the current line needs to be restrained
                if cfg.yes == jnts_to_rstrt[jnt_id][cfg.u1]:
                    rmk_line_ndl_pnt['N1'] = 1
                if cfg.yes == jnts_to_rstrt[jnt_id][cfg.u3]:
                    rmk_line_ndl_pnt['N2'] = 1
                if cfg.yes == jnts_to_rstrt[jnt_id][cfg.u2]:
                    rmk_line_ndl_pnt['N3'] = 1
                    # NOTE: Ruaumoko swaps the y-axis and z-axis
                
                if cfg.yes == jnts_to_rstrt[jnt_id][cfg.r1]:
                    rmk_line_ndl_pnt['N4'] = 1
                if cfg.yes == jnts_to_rstrt[jnt_id][cfg.r3]:
                    rmk_line_ndl_pnt['N5'] = 1
                if cfg.yes == jnts_to_rstrt[jnt_id][cfg.r2]:
                    rmk_line_ndl_pnt['N6'] = 1
                    # NOTE: Ruaumoko swaps the y-axis and z-axis
                
            raw_strct_ndl_pnt.update({jnt_id : rmk_line_ndl_pnt})
            stry_data.update(self.stry_data)
            
        return raw_strct_ndl_pnt, stry_data