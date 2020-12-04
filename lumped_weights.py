# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 22:20:44 2019

@author: alvin
"""

import collections
import numpy as np
import copy

import config as cfg
from config import data_retriever

def convert(weight_instances):
    """ This function returns the centre of mass nodes for monitoring drift 
    of each diaphragm group (storey), lumped nodal weights nodal no. and the 
    weights of the 6 DoFs (visibility can be adjusted in config.py), and the  
    static loads nodal no. and the weights of the 6 DoFs (visibility can be  
    adjusted in config.py). """
    raw_ndl_drft = []
    raw_ndl_wgt = []
    raw_sttc_ld = []
    
    for weight_inst in weight_instances:
        com_nd = str(weight_inst.nd_l)
        line_ndl_wgt = [com_nd]
        line_sttc_ld = [com_nd]
        
        for dof, flag in cfg.weights_dofs.items():
            if bool(flag):
                dof_weight = str(round(weight_inst.com_nd_weights[dof],4))
                line_ndl_wgt.append(dof_weight)
            else:
                line_ndl_wgt.append('0')
        
        for dof, flag in cfg.loads_dofs.items():
            if bool(flag):
                dof_weight = str(round(weight_inst.com_nd_weights[dof],4))
                line_sttc_ld.append(dof_weight)
            else:
                line_sttc_ld.append('0')
                
        raw_ndl_drft.append(com_nd)
        raw_ndl_wgt.append('\t'.join(line_ndl_wgt))
        raw_sttc_ld.append('\t'.join(line_sttc_ld))
        
    rmk_ndl_drft = '\t'.join(raw_ndl_drft)
    rmk_ndl_wgt = '\n'.join(raw_ndl_wgt)
    rmk_sttc_ld = '\n'.join(raw_sttc_ld)
    
    return rmk_ndl_drft, rmk_ndl_wgt, rmk_sttc_ld

def get_com(s2k_data, rfd_diaph, stry_data, raw_strct_ndl_pnt):
    """
    Converts the s2k joint masses to rmk nodal weights and static loads. 
    This is the main function of this module which executes the other functions.
    """
    rfd_diaph = copy.deepcopy(rfd_diaph)
    rfd_diaph = collections.OrderedDict(sorted(rfd_diaph.items()))
    raw_grav_ndl_pnt = {}
    
    # Organize the joint masses for use later
    s2k_jnt_masses = data_retriever(s2k_data, cfg.title_joint_masses)
    get_jnt_masses = {line[cfg.jnt_masses] : line for line in s2k_jnt_masses}
    
    # Organize the joint elements
    s2k_jnt_elem = data_retriever(s2k_data, cfg.title_joint_elements)
    get_jnt_elem = {}
    get_jnt_coords = {}
    
    for line in s2k_jnt_elem:
        elem_id = line[cfg.jnt_elem]
        coords = {'X' : round(float(line[cfg.x]), 4), 
                  'Y' : round(float(line[cfg.z]), 4), 
                  'Z' : round(float(line[cfg.y]), 4)}
            # NOTE: Ruaumoko swaps the y-axis and z-axis
        
        if coords['Y'] not in get_jnt_elem.keys():
            get_jnt_elem.update({coords['Y'] : [elem_id]})
        else:
            get_jnt_elem[coords['Y']].append(elem_id)
        
        get_jnt_coords.update({elem_id : coords})
    
    # Define the lumped weight instances
    weight_instances = []
    get_com = {}
    
    for idx, (diaph_id, diaph_jnts) in enumerate(rfd_diaph.items()):
        weight_instances.append(LumpedWeight(idx))
        weight_inst = weight_instances[idx]
        
        # Add the shell inner joints to the diaph_jnts based on the z-coord of
        # the first joint in diaph_jnts
        nd_no = raw_strct_ndl_pnt[diaph_jnts[0]]['N']
        Y_coord = stry_data[nd_no]['Y']
        diaph_jnts.extend(get_jnt_elem[Y_coord])
        
        # Calculate the centre of mass coordinates
        generate_com_nd(weight_inst, get_jnt_masses, diaph_jnts, get_jnt_coords)
        
        # Calculate the rotational inertia weights for the lumped mass node
        calculate_rot_wgts(weight_inst, get_jnt_masses, diaph_jnts, get_jnt_coords)
        
        # Set the node k and node l for the gravity columns
        if idx == 0:
            raw_grav_ndl_pnt = weight_inst.set_node_l(raw_grav_ndl_pnt, 
                                                       'foundation')
        else:
            raw_grav_ndl_pnt = weight_inst.set_node_k(raw_grav_ndl_pnt)
            raw_grav_ndl_pnt = weight_inst.set_node_l(raw_grav_ndl_pnt)
        
        # Update the master diaphragm node
        get_com.update({diaph_id : weight_inst.nd_l})
    
    raw_grav_ndl_pnt.update(raw_strct_ndl_pnt)
    
    return weight_instances, raw_grav_ndl_pnt, get_com

def generate_com_nd(weight_inst, get_jnt_masses, diaph_jnts, get_jnt_coords):
    """ Find the position of the centre of mass (com) at the given diaphragm 
    group (diaph_jnts) and generate a rmk nodal point input for it. """
    trans_masses = np.array([0.0, 0.0, 0.0])    # array(x, y, z)
    sum_numerator = [0, 0, 0]                   # [x, y, z]
    sum_denominator = [0, 0, 0]                 # [x, y, z]

    for joint in diaph_jnts:
        jnt_masses = get_jnt_masses[joint]
        coords = get_jnt_coords[joint]
        
            # Get the nodal translational masses for (x, y, z)
        ndl_masses = np.array([float(jnt_masses[cfg.ux_masses]), 
                               float(jnt_masses[cfg.uz_masses]), 
                               float(jnt_masses[cfg.uy_masses])])
            # NOTE: Ruaumoko swaps the y-axis and z-axis
        
        # Calculate the x-axis weight
        sum_numerator[0] += coords['X'] * ndl_masses[0]
        sum_denominator[0] += ndl_masses[0]
    
        # Calculate the y-axis weight
        sum_numerator[1] += coords['Y'] * ndl_masses[1]
        sum_denominator[1] += ndl_masses[1]
    
        # Calculate the z-axis weight
        sum_numerator[2] += coords['Z'] * ndl_masses[2]
        sum_denominator[2] += ndl_masses[2]
                
        trans_masses += ndl_masses
        
    trans_weights = trans_masses * 9.81 / 2 # NOTE: The divided by 2 is a temporary fix because diaph_jnts actually included the same joints twice.
    weight_inst.com_nd_weights.update({'ux' : trans_weights[0], 
                                       'uy' : trans_weights[1], 
                                       'uz' : trans_weights[2]})
    
    weight_inst.com_coords = {'X' : safe_div(sum_numerator[0], sum_denominator[0]), 
                              'Y' : safe_div(sum_numerator[1], sum_denominator[1]), 
                              'Z' : safe_div(sum_numerator[2], sum_denominator[2])}

def calculate_rot_wgts(weight_inst, get_jnt_masses, diaph_jnts, get_jnt_coords):
    """ Generate the weights associated with rotations (rx, ry, rz) for the 
    lumped weight node. """
    rot_inertia = np.array([0.0, 0.0, 0.0])     # array(x, y, z)
        
    for joint in diaph_jnts:
        jnt_masses = get_jnt_masses[joint]
        coords = get_jnt_coords[joint]
        
            # Get the nodal translational masses for (x, y, z)
        ndl_masses = np.array([float(jnt_masses[cfg.ux_masses]), 
                               float(jnt_masses[cfg.uz_masses]), 
                               float(jnt_masses[cfg.uy_masses])])
            # NOTE: Ruaumoko swaps the y-axis and z-axis
        
        # Calculate the rotational inertia
        x_r_sqrd = 0; y_r_sqrd = 0; z_r_sqrd = 0
        
        if bool(cfg.weights_dofs['rx']):
            # x-axis rotational inertia
            y_diff = weight_inst.com_coords['Y'] - coords['Y']
            z_diff = weight_inst.com_coords['Z'] - coords['Z']
            x_r_sqrd = y_diff ** 2 + z_diff ** 2
            
        if bool(cfg.weights_dofs['ry']):
            # y-axis rotational inertia
            x_diff = weight_inst.com_coords['X'] - coords['X']
            z_diff = weight_inst.com_coords['Z'] - coords['Z']
            y_r_sqrd = x_diff ** 2 + z_diff ** 2
            
        if bool(cfg.weights_dofs['rz']):
            # z-axis rotational inertia
            x_diff = weight_inst.com_coords['X'] - coords['X']
            y_diff = weight_inst.com_coords['Y'] - coords['Y']
            z_r_sqrd = x_diff ** 2 + y_diff ** 2
    
        r_sqrd = np.array([x_r_sqrd, y_r_sqrd, z_r_sqrd])
        rot_inertia += ndl_masses * r_sqrd
    
    rot_weights = rot_inertia * 9.81
    weight_inst.com_nd_weights.update({'rx' : rot_weights[0], 
                                       'ry' : rot_weights[1], 
                                       'rz' : rot_weights[2]})
    
def safe_div(x, y):
    """ This function divides x/y and returns zero when ZeroDivisionError. """
    if y == 0:
        print('Warning: Ensure that the nodes in each diaphragm group have ' + 
              'masses assigned...')
        return 0
    return x/y

class LumpedWeight:
    """
    A LumpedWeight instance contains the centre of mass for a diaphragm constraint
    group, as well as all the translational and rotational masses.
    """
    def __init__(self, diaph_idx):
        """ Initializer to set the lumped weight ID, which is also the 
        diaphragm ID. """
        self.diaph_idx = diaph_idx
        self.com_coords = {}            # {x, y, z}
        self.com_nd_weights = {}        # {ux, uy, uz, rx, ry, rz}
        
    def __str__(self):
        """ For print() and str() """
        return 'This instance has an ID of: {}'.format(self.diaph_idx)
    
    def __repr__(self):
        """ For repr() and interactive prompt """
        return 'LumpedWeight(diaph_idx={})'.format(self.diaph_idx)
    
    def set_node_l(self, raw_strct_ndl_pnt, level = 'default'):
        """ Set the rmk nodal point input for node l (CoM node) or END2 of  
        the gravity column. Then updates the raw_strct_ndl_pnt. """
        self.nd_l = len(raw_strct_ndl_pnt) + 1
        
        x = round(self.com_coords['X'], 3)
        y = round(self.com_coords['Y'], 3)
        z = round(self.com_coords['Z'], 3)
        
        if level == 'foundation':
            raw_strct_ndl_pnt.update({'{}: nd_l'.format(self.diaph_idx) : {
                    'N':self.nd_l, 'X':x, 'Y':y, 'Z':z, 'N1':1, 'N2':1, 'N3':1, 
                    'N4':1, 'N5':1, 'N6':1, 'KUP1':0, 'IOUT':0, 'KUP2':0}})
        else:
            raw_strct_ndl_pnt.update({'{}: nd_l'.format(self.diaph_idx) : {
                    'N':self.nd_l, 'X':x, 'Y':y, 'Z':z, 'N1':0, 'N2':3, 'N3':0, 
                    'N4':1, 'N5':0, 'N6':1, 'KUP1':0, 'IOUT':0, 
                    'KUP2':(self.nd_l - 1)}})
    
        return raw_strct_ndl_pnt
    
    def set_node_k(self, raw_strct_ndl_pnt):
        """ Set the rmk nodal point input for node k or END1 of the gravity
        column. The y coord (vertical) is the same as that of the level below. 
        Then updates the raw_strct_ndl_pnt. """
        self.nd_k = len(raw_strct_ndl_pnt) + 1
        
        x = round(self.com_coords['X'], 3)
        y = raw_strct_ndl_pnt['{}: nd_l'.format(self.diaph_idx-1)]['Y']
        z = round(self.com_coords['Z'], 3)
        
        raw_strct_ndl_pnt.update({'{}: nd_k'.format(self.diaph_idx) : {
                'N':self.nd_k, 'X':x, 'Y':y, 'Z':z, 'N1':0, 'N2':3, 'N3':0, 
                'N4':1, 'N5':0, 'N6':1, 'KUP1':0, 'IOUT':0, 
                'KUP2':(self.nd_k - 1)}})
    
        return raw_strct_ndl_pnt