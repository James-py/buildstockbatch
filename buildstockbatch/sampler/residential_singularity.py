# -*- coding: utf-8 -*-

"""
buildstockbatch.sampler.residential_singularity
~~~~~~~~~~~~~~~
This object contains the code required for generating the set of simulations to execute

:author: Noel Merket, Ry Horsey
:copyright: (c) 2018 by The Alliance for Sustainable Energy
:license: BSD-3
"""

import logging
import os
import subprocess


from .base import BuildStockSampler

logger = logging.getLogger(__name__)


class ResidentialSingularitySampler(BuildStockSampler):

    def __init__(self, singularity_image, output_dir, *args, **kwargs):
        """
        Initialize the sampler.

        :param singularity_image: path to the singularity image to use
        :param output_dir: Simulation working directory
        :param cfg: YAML configuration specified by the user for the analysis
        :param buildstock_dir: The location of the resstock or comstock repo
        :param project_dir: The project directory within the resstock or comstock repo
        """
        super().__init__(*args, **kwargs)
        self.singularity_image = singularity_image
        self.output_dir = output_dir
        self.csv_path = os.path.join(self.output_dir, 'housing_characteristics', 'buildstock.csv')

    def run_sampling(self, n_datapoints):
        """
        Run the residential sampling in a singularity container.

        :param n_datapoints: Number of datapoints to sample from the distributions.
        :return: Absolute path to the output buildstock.csv file
        """
        logger.debug('Sampling, n_datapoints={}'.format(n_datapoints))
        args = [
            'singularity',
            'exec',
            '--contain',
            '--home', '{}:/buildstock'.format(self.buildstock_dir),
            '--bind', '{}:/outbind'.format(os.path.dirname(self.csv_path)),
            self.singularity_image,
            'ruby',
            'resources/run_sampling.rb',
            '-p', self.cfg['project_directory'],
            '-n', str(n_datapoints),
            '-o', '../../outbind/{}'.format(os.path.basename(self.csv_path))
        ]
        logger.debug(f"Starting singularity sampling with command: {' '.join(args)}")
        subprocess.run(args, check=True, env=os.environ, cwd=self.output_dir)
        logger.debug("Singularity sampling completed.")
        return self.csv_path
