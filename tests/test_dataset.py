#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests.test_dataset

test submodules for runtime errors

Author: Jacob Reinhold (jacob.reinhold@jhu.edu)

Created on: Oct 24, 2018
"""

import os
import shutil
import tempfile
import unittest

import torchvision.transforms as torch_tfms

from niftidataset import *

try:
    import fastai
except ImportError:
    fastai = None


class TestUtilities(unittest.TestCase):

    def setUp(self):
        wd = os.path.dirname(os.path.abspath(__file__))
        self.nii_dir = os.path.join(wd, 'test_data', 'nii')
        self.tif_dir = os.path.join(wd, 'test_data', 'tif')
        self.out_dir = tempfile.mkdtemp()
        self.train_dir = os.path.join(self.out_dir, 'train')
        os.mkdir(self.train_dir)
        os.mkdir(os.path.join(self.train_dir, '1'))
        os.mkdir(os.path.join(self.train_dir, '2'))
        nii = glob_nii(self.nii_dir)[0]
        tif = os.path.join(self.tif_dir, 'test.tif')
        path, base, ext = split_filename(nii)
        for i in range(4):
            shutil.copy(nii, os.path.join(self.train_dir, base + str(i) + ext))
            shutil.copy(tif, os.path.join(self.train_dir, '1', base + str(i) + '.tif'))
            shutil.copy(tif, os.path.join(self.train_dir, '2', base + str(i) + '.tif'))

    def test_niftidataset_2d(self):
        composed = torch_tfms.Compose([RandomCrop2D(10, 0),
                                       ToTensor(),
                                       Normalize()])
        myds = NiftiDataset(self.train_dir, self.train_dir, composed)
        self.assertEqual(myds[0][0].shape, (1,10,10))

    def test_niftidataset_2d_slice(self):
        composed = torch_tfms.Compose([RandomSlice(0),
                                       ToTensor()])
        myds = NiftiDataset(self.train_dir, self.train_dir, composed)
        self.assertEqual(myds[0][0].shape, (1,64,64))

    def test_niftidataset_3d(self):
        composed = torch_tfms.Compose([RandomCrop3D(10),
                                       ToTensor()])
        myds = NiftiDataset(self.train_dir, self.train_dir, composed)
        self.assertEqual(myds[0][0].shape, (1,10,10,10))

    def test_niftidataset_preload(self):
        composed = torch_tfms.Compose([RandomCrop3D(10),
                                       ToTensor(),
                                       AddChannel()])
        myds = NiftiDataset(self.train_dir, self.train_dir, composed, preload=True)
        self.assertEqual(myds[0][0].shape, (1,1,10,10,10))
        
    def test_multimodalnifti_2d(self):
        composed = torch_tfms.Compose([RandomCrop2D(10, 0),
                                       ToTensor(),
                                       Normalize()])
        sd, td = [self.train_dir] * 3, [self.train_dir]
        myds = MultimodalNiftiDataset(sd, td, composed)
        self.assertEqual(myds[0][0].shape, (3,10,10))
        self.assertEqual(myds[0][1].shape, (1,10,10))

    def test_multimodalnifti_slice(self):
       composed = torch_tfms.Compose([RandomSlice(0),
                                      ToTensor()])
       sd, td = [self.train_dir] * 2, [self.train_dir] * 4
       myds = MultimodalNiftiDataset(sd, td, composed)
       self.assertEqual(myds[0][0].shape, (2,64,64))
       self.assertEqual(myds[0][1].shape, (4,64,64))

    def test_multimodalnifti_3d(self):
        composed = torch_tfms.Compose([RandomCrop3D(10),
                                       ToTensor()])
        sd, td = [self.train_dir] * 3, [self.train_dir] * 2
        myds = MultimodalNiftiDataset(sd, td, composed)
        self.assertEqual(myds[0][0].shape, (3,10,10,10))
        self.assertEqual(myds[0][1].shape, (2,10,10,10))
    
    def test_multimodaltiff(self):
        composed = torch_tfms.Compose([ToTensor()])
        sd, td = [self.train_dir+'/1/'] * 3, [self.train_dir+'/2/'] * 2
        myds = MultimodalTiffDataset(sd, td, composed)
        self.assertEqual(myds[0][0].shape, (3,256,256))
        self.assertEqual(myds[0][1].shape, (2,256,256))
   
    @unittest.skipIf(fastai is None, "fastai is not installed on this system")
    def test_niftidataset_2d_fastai(self):
        composed = torch_tfms.Compose([RandomCrop2D(10, 0),
                                       ToTensor(),
                                       ToFastaiImage()])
        myds = NiftiDataset(self.train_dir, self.train_dir, composed)
        self.assertEqual(myds[0][0].shape, (1,10,10))

    @unittest.skipIf(fastai is None, "fastai is not installed on this system")
    def test_tifftuplelist(self):
        from niftidataset.fastai import TIFFTupleList
        data = (TIFFTupleList.from_folders(self.train_dir, '1', '2', extensions=('.tif'))
                             .no_split()
                             .label_const(0.)
                             .transform()
                             .databunch(bs=4))
        data.valid_dl = None
        print(data.train_ds[0])
        data.show_batch(rows=1)
        self.assertEqual(data.train_ds[0][0].data[0].shape, (1,256,256))
        
    def tearDown(self):
        shutil.rmtree(self.out_dir)


if __name__ == '__main__':
    unittest.main()
