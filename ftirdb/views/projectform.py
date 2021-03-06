"""

Project: FTIRDB
File: views/graph.py

Version: v1.0
Date: 10.09.2018
Function: provides functions required for addAccount view

This program is released under the GNU Public Licence (GPL V3)

--------------------------------------------------------------------------
Description:

Contains functions required for viewing graphs based on jcamp files



============


"""
from pyramid.compat import escape
import re
from docutils.core import publish_parts
import matplotlib.pyplot as plt
from jcamp import JCAMP_reader, JCAMP_calc_xsec
import colander 
import deform
import peppercorn
import numpy
import requests
from deform import Form, FileData
import os
from sqlalchemy import event
from sqlalchemy import *
from sqlalchemy.databases import mysql
from sqlalchemy.orm import relation, backref, synonym
from sqlalchemy.orm.exc import NoResultFound
import colanderalchemy
from colanderalchemy import setup_schema
import pathlib
from pathlib import Path

import numpy as np

from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound,
    HTTPNotFound,
    )

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.response import Response
import deform
import colander
from deform import widget

from ..models import project, experiment, spectrometer, post_processing_and_deposited_spectra, spectra, sample, publication


#view for the project form, including publication form
@view_config(route_name='projectform', renderer='../templates/projectform.jinja2')
def projectform(request):
    
    """ project form page """
    #create the schema using colander alchemy
    class All(colander.MappingSchema):
        setup_schema(None,project)
        projectSchema=project.__colanderalchemy__
        setup_schema(None,publication)
        publicationSchema=publication.__colanderalchemy__
        

    
    # create the form using deform
    form = deform.Form(All(),buttons=('submit',))
        
    
    if 'submit' in request.POST:
        
        #retreive results and deserialize using peppercorn
        controls = request.POST.items()
        pstruct = peppercorn.parse(controls)

     


        try:
                # call validate
                appstruct = form.validate(controls)

                #if no exceptions then add data to databank - pstruct must come after validation for error form to render
                descriptive_name = request.params['descriptive_name']
                related_experiments_ID = request.params['related_experiments_ID']
                print(pstruct)
                items = pstruct['publicationSchema']
               
                page = project(descriptive_name=descriptive_name,related_experiments_ID=related_experiments_ID)

                
                request.dbsession.add(page)
                
                project_id = request.dbsession.query(project).order_by(project.project_ID.desc()).first()
                project_id = project_id.project_ID
                page = publication(experiment_ID=project_id,**items)
                request.dbsession.add(page)
                #return project page 
                next_url = request.route_url('projectPage', pagename=project_id)
                return HTTPFound(location=next_url)
             
        except deform.ValidationFailure as e: # catch the exception
                return {'projectForm':e.render()}
           

        
    
    else:
        #render the form
        projectForm = form.render()
        return{'projectForm':projectForm}
    
@view_config(route_name='projectPage', renderer='../templates/projectPage.jinja2')

def projectPage(request):

    """This page takes a project with project_ID in the URL and returns a page with a dictionary of
all the values for the project, associated experiments and publication data, it also contains buttons for adding samples and experiments."""

    if 'submitted' in request.params:
        
        
        if request.params['submitted'] == 'Add sample':
            #retrieve project ID and send to sample page
            search = request.matchdict['pagename']
            next_url = request.route_url('sampleForm2',project_ID=search)
            return HTTPFound(location=next_url)
            
        else:
            search = request.matchdict['pagename']
            next_url = request.route_url('experimentForm2',project_ID=search)
            return HTTPFound(location=next_url)
            
        
        
        
    else:
        search = request.matchdict['pagename']
    #return project related to ID 
        
        searchdb = request.dbsession.query(project).filter_by(project_ID=search).all()
        dic = {}
        for u in searchdb:
            new = u.__dict__
            dic.update( new )
        
        
        searchexp = request.dbsession.query(experiment).filter_by(project_ID=search).all()
        
        expdic = {}
        #return related experiments as a dictionary
        for u in searchexp:
            new = u.__dict__
            expdic.update( new )
      
    #return samples related to ID in a dictionary

       
        samples = {}
            
        search2 = request.dbsession.query(sample.sample_ID).filter_by(project_ID=search).all()
        
        for u in search2:
            num = u[0]
            samples[ 'sample' + str(num)] = num
           
        
        
    #return spectra related to ID in a dictionary
        #need to return spectra ID and use for getting data from ppd
    # return experiment data
        exp_ID = request.dbsession.query(experiment.experiment_ID).filter_by(project_ID=search).first()
        
        try:
            searchexp2 = request.dbsession.query(experiment.experiment_ID).filter_by(project_ID=search).all()
            exp_ID = exp_ID[0]
        except:
            exp_ID = 0
        print('here')
   
        print(searchexp2)
        exper = {}
    
        # just return related experiment ID's
        for u in searchexp2:
            num = u[0]
            exper[ 'experiment' + str(num)] = num
           
       
    #return spectra detail
        spectradic = {}
        search = request.dbsession.query(spectra).filter_by(experiment_ID=exp_ID).all()
        for u in search:
            new = u.__dict__
            spectradic.update( new )
        
        try:
            also = request.dbsession.query(spectra.spectra_ID).filter_by(experiment_ID=exp_ID).first()
            ppd_ID = also[0]
       
        except:
            ppd_ID = 0
            
        # need to fix this 
      
     
        #for some reason the spectra_ID in ppd are all 1
        
        search2 = request.dbsession.query(post_processing_and_deposited_spectra).filter_by(spectra_ID=ppd_ID).all()
        depodic = {}
        for u in search2: 
            new = u.__dict__
            depodic.update( new )
      
        
    # spectrometer information
      
        spectrodic = {}
        search = request.dbsession.query(spectrometer).filter_by(experiment_ID=exp_ID).all()
        for u in search:
            new = u.__dict__
            spectrodic.update( new )
        
        
        publicationdic = {}
        search = request.matchdict['pagename']
        print('here')
        print(search)
        search = request.dbsession.query(publication).filter_by(experiment_ID=search).all()
        for u in search:
            new = u.__dict__
            publicationdic.update( new )
        
       
     

        

        return {'dic': dic , 'expdic':expdic,'exper':exper,'samples':samples, 'publication':publicationdic}
    
    
    
