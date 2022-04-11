#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 17:44:45 2021

@author: linkv
"""
import numpy as np
import pandas as pd

class TVariants:
    def __init__(self, ts_object, samp_ids):
        self.number = len(np.array(ts_object.variants(samples=samp_ids)))
        self.positions = np.empty(self.number)
        self.alleleFreq = np.empty(self.number)
        
        for v, var in enumerate(list(ts_object.variants(samples=samp_ids))):  
            tmp = sum(var.genotypes) / len(var.genotypes)
            af = min(tmp, 1-tmp)
            
            self.positions[v] = var.site.position
            self.alleleFreq[v] = af
        
    def writeVariantInfo(self, ts_object, samp_ids, name):
        table = pd.DataFrame()
        table['var_index'] = np.arange(self.number)
        table['position'] = self.positions
        table['allele_freq'] = self.alleleFreq
        
        table.to_csv(name + "_simulated_sample_variants.csv", header=True, index=False)
        
class TVariantsFiltered(TVariants):
    
    def __init__(self, ts_object, samp_ids, min_allele_freq, max_allele_freq, prop_typed_variants, pos_int, random, logfile, filtered_variants_file = None):
        
        """
        When should the filtered_variants_file be provided? If it is provided, the allele frequencies will be the original allele frequencies and the typed status will be predefined
        Also they may also already be filtered for min and max freq. However, they may not match the tree file?
        """
        
        # TODO: I don't understand if I should use the variants as a list or not. I don't know how to save them if not as a list (self.variants = trees.variants() or trees.variants does not work. maybe as np.array? but then enumerate in TPhenotypes does not work
        self.variants = list(ts_object.variants(samples=samp_ids))
        self.number = -1
        self.number_typed = -1
        
        #build variant object from tree file -> filter!
        if filtered_variants_file is None:

            logfile.info("- Building variant information from scratch based on simulated trees")

            if min_allele_freq < 0 or max_allele_freq < 0 or min_allele_freq > 1 or max_allele_freq > 1 or min_allele_freq > max_allele_freq:
                raise ValueError("allele frequency filters are nonsensical")
            
            #initialize
            self.number = len(list(ts_object.variants(samples=samp_ids)))
            self.info = pd.DataFrame(index=range(self.number),columns=['var_index', 'position', 'allele_freq', 'typed'])  
           
            #fill by filtering, can't directly fill into info table because number of variants is unknown
            for v, var in enumerate(ts_object.variants(samples=samp_ids)):
                tmp = sum(var.genotypes) / len(var.genotypes)
                af = min(tmp, 1-tmp)
                
                # add position
                pos = -1
                if pos_int == True:
                    pos = round(var.site.position)
                    if v > 0 and pos == self.info['position'][v-1]:
                        # print("am in special case for v", v)
                        pos += 1
                else:
                    pos = var.site.position
                
                #is variant typed?
                if af >= min_allele_freq and af <= max_allele_freq:
                    if prop_typed_variants == 1:
                        typed = True                        
                    else:
                        r = random.random.uniform(0,1,1)
                        if r < prop_typed_variants:
                            typed = True
                        else: 
                            typed = False
                else:
                    typed = False
                    
                #add to table
                self.info.iloc[v] = [v, pos, af, typed]
        
        #variants are already filtered -> read from file!
        else:
            logfile.info("- Reading variant information from " + filtered_variants_file)
            self.info = pd.read_csv(filtered_variants_file)
            
            #rename if variant file is in old format
            if 'index' in self.info.columns:
                self.info.rename(columns={'index': 'var_index'}, inplace = True)         
          
        #set number typed
        self.number = len(self.info['typed'])
        self.number_typed = self.info['typed'].value_counts()[True]
        if len(self.info['var_index']) != self.number != len(self.variants):
            raise ValueError("Variant file " + filtered_variants_file + " contains " + str(len(self.info['var_index'])) + " variants, expected " + str(self.number))
            
        #set indeces of trees the variants belong to
        self.info['tree_index'] = np.digitize(self.info['position'], ts_object.breakpoints(as_array=True))

                 
    def print_genotypes(self, index):        
        file = "genotypes_variant" + str(index) + ".txt"
        self.info['variant'][index].genotypes.tofile(file=file)
        
    def fill_diploidGenotypes(self, individuals):
        for v in self.info['variant']:
            v.site.metadata = []
                        
    def writeVariantInfo(self, name, logfile):    
        logfile.info("- Writing variant info to file '" + name + "_filtered_sample_variants.csv'")
        self.info.to_csv(name + "_filtered_sample_variants.csv", header=True, index=False)
        
    def writeShapeit2(self, name, inds, logfile):
        """
        Write files in SHAPEIT2 format, to be used as input by RELATE (https://myersgroup.github.io/relate/input_data.html)

        Parameters
        ----------
        name : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        haps = pd.DataFrame(index=range(self.number_typed),columns=range(5 + inds.num_haplotypes)) 
        info_typed = self.info.loc[self.info['typed'] == True]
        info_typed['index'] = range(self.number_typed)
        info_typed.set_index(info_typed['index'], drop=True, inplace=True)
                
        haps.iloc[:, 0] = np.repeat(1, self.number_typed)
        haps.iloc[:, 1] = '.'
        haps.iloc[0:self.number_typed, 2] = info_typed['position']
        haps.iloc[:, 3] = 'A'
        haps.iloc[:, 4] = 'T'
        
        logfile.info("- Building haplotypes for typed variants")
        
        index = 0
        for v, var in enumerate(self.variants):
            # print(v, self.info.iloc[v]['typed'])
            if self.info.iloc[v]['typed'] == True:
                # if self.info.iloc[v]['position'] == None :
                #     print(self.info.iloc[v])
                haps.iloc[index,5:] = var.genotypes #can't use v for index because it loops over all variants, not only typed ones
                # if index in [9,10, 11, 12]:
                #     print("v", v, "positions\n", self.info.iloc[v])
                index += 1
        
        logfile.info("- Writing haplotypes in Shapeit2 format to file '" + name + "_variants.haps'")
        haps.to_csv(name + "_variants.haps", sep=' ', header=False, index=False)
        
        
    def findVariant(self, typed, freq, interval, out, subplot, random, logfile):
        """
        Find a variant that fits criteria to simulate fixed genotype depending on only one variant

        Parameters
        ----------
        typed : bool
            Should the variant returned be typed or not.
        freq : float
            Requested allele frequency of the variant. If there is no variant with this exact frequency within the requested interval, 0.001 will be deducted from the freq repeatedly until a variant is found.
        interval : list of floats
            Requested genomic interval within which the variant should be.

        Raises
        ------
        ValueError
            If the search for a variant within the requested genomic interval ends up with the allele freq being negative, the search is stopped an an error is thrown.

        Returns
        -------
        Index of the variant found, can be used to simulate fixed phenotype.

        """
        
                
        # check if interval is valid
        num_lines = self.info[(self.info['position'] >= interval[0]) & (self.info['position'] <= interval[1])].shape[0]
        if num_lines == 0:
            raise ValueError("The interval " + str(interval) + " contains no variants")
                
        # make subset of variants in interval
        info_interval = self.info.loc[(self.info['position'] >= interval[0]) & (self.info['position'] <= interval[1])]
        # info_interval['index'] = range(self.info[(self.info['position'] >= interval[0]) & (self.info['position'] <= interval[1])].shape[0])
        # info_interval.set_index(info_interval['index'], drop=True, inplace=True)
                           
        # check if there are variants with requested typed status
        num_lines = info_interval[info_interval['typed'] == typed].shape[0]
        if num_lines == 0:
            raise ValueError("There are no variants of typed status '" + str(typed) +"'")
            
        # make subset of variants in interval with correct typed status
        info_interval = info_interval.loc[info_interval['typed'] == typed]
        # info_interval['index'] = range(num_lines)
        # info_interval.set_index(info_interval['index'], drop=True, inplace=True)
        
        # plot allele freq spectrum
        n, bins, patches = subplot.hist(info_interval['allele_freq'], density=False)
        subplot.axvline(x = freq, color = "red", lw = 1)
        subplot.set(xlabel='Allele freq', ylabel='count', title = 'Histogram of af in requested interval and typed status')

        # find first variant with requested allele frequency
        info = info_interval[np.isclose(np.array(info_interval['allele_freq'], dtype = float), freq, rtol=0.01)]
        
        if info.shape[0] < 1:
            logfile.info("- Did not find locus with requested af " + str(freq) + ". Adapting af in increments of 0.001.")
        
            #set direction of search
            r = random.random.uniform(0,1,1)
            if r < 0.5:
                step = -0.001
            else:
                step = 0.001
                
            freq_orig = freq
                
            while info.shape[0] < 1 and freq >= 0 and freq <= 0.5:
                #remove or add small value to freq until a locus is found
                freq = round(freq + step,3) 
                info = info_interval[np.isclose(np.array(info_interval['allele_freq'], dtype = float), freq, rtol=0.01)]
            
            #if loop was left because out of bounds, search in other direction
            if freq < 0 or freq > 0.5:
                logfile.warning("Allele frequency became negative or exceeded 0.5 while searching for locus with requested af " + str(freq_orig) + " in interval " + str(interval) + ". Starting search in opposite direction.")
                step = -step
                
                #set search back to starting freq and go in other direction
                freq = freq_orig
    
                while info.shape[0] < 1 and freq >= 0 and freq <= 0.5:
                    freq = round(freq + step,3)    
                    info = info_interval[np.isclose(np.array(info_interval['allele_freq'], dtype = float), freq, rtol=0.01)]
    
            if freq < 0 or freq > 0.5:
                raise ValueError("Could not find locus with requested allele frequency")
            
        subplot.axvline(x = freq, color = "black", lw = 1)


        # logfile.info("--> Found variant with freq " + str(freq) + " within the following interval: " + str(interval))
        return info.iloc[0]['var_index'], info.iloc[0]['position']
