# -*- coding: utf-8 -*-

"""
buildstockbatch.workflow_generator.residential_hpxml
~~~~~~~~~~~~~~~
This object contains the residential classes for generating OSW files from individual samples

:author: Joe Robertson
:copyright: (c) 2021 by The Alliance for Sustainable Energy
:license: BSD-3
"""

import datetime as dt
import json
import logging
import re
import yamale

from .base import WorkflowGeneratorBase

logger = logging.getLogger(__name__)


class ResidentialHpxmlWorkflowGenerator(WorkflowGeneratorBase):

    @classmethod
    def validate(cls, cfg):
        """Validate arguments

        :param cfg: project configuration
        :type cfg: dict
        """
        schema_yml = """
        measures_to_ignore: list(str(), required=False)
        build_existing_model: map(required=False)
        emissions: list(include('emission-scenario-spec'), required=False)
        utility_bills: list(include('utility-bill-scenario-spec'), required=False)
        measures: list(include('measure-spec'), required=False)
        reporting_measures: list(include('measure-spec'), required=False)
        simulation_output_report: map(required=False)
        server_directory_cleanup: map(required=False)
        debug: bool(required=False)
        ---
        emission-scenario-spec:
            scenario_name: str(required=True)
            type: str(required=True)
            elec_folder: str(required=True)
            gas_value: num(required=False)
            propane_value: num(required=False)
            oil_value: num(required=False)
            wood_value: num(required=False)
        utility-bill-scenario-spec:
            scenario_name: str(required=True)
            elec_fixed_charge: num(required=False)
            elec_marginal_rate: num(required=False)
            gas_fixed_charge: num(required=False)
            gas_marginal_rate: num(required=False)
            propane_fixed_charge: num(required=False)
            propane_marginal_rate: num(required=False)
            oil_fixed_charge: num(required=False)
            oil_marginal_rate: num(required=False)
            wood_fixed_charge: num(required=False)
            wood_marginal_rate: num(required=False)
            pv_compensation_type: str(required=False)
            pv_net_metering_annual_excess_sellback_rate_type: str(required=False)
            pv_net_metering_annual_excess_sellback_rate: num(required=False)
            pv_feed_in_tariff_rate: num(required=False)
            pv_monthly_grid_connection_fee_units: str(required=False)
            pv_monthly_grid_connection_fee: num(required=False)
        measure-spec:
            measure_dir_name: str(required=True)
            arguments: map(required=False)
        """
        workflow_generator_args = cfg['workflow_generator']['args']
        schema_yml = re.sub(r'^ {8}', '', schema_yml, flags=re.MULTILINE)
        schema = yamale.make_schema(content=schema_yml, parser='ruamel')
        data = yamale.make_data(content=json.dumps(workflow_generator_args), parser='ruamel')
        yamale.validate(schema, data, strict=True)
        return True

    def reporting_measures(self):
        """Return a list of reporting measures to include in outputs"""
        workflow_args = self.cfg['workflow_generator'].get('args', {})
        return [x['measure_dir_name'] for x in workflow_args.get('reporting_measures', [])]

    def create_osw(self, sim_id, building_id, upgrade_idx):
        """
        Generate and return the osw as a python dict

        :param sim_id: simulation id, looks like 'bldg0000001up01'
        :param building_id: integer building id to use from the sampled buildstock.csv
        :param upgrade_idx: integer index of the upgrade scenario to apply, None if baseline
        """
        # Default argument values
        workflow_args = {
            'build_existing_model': {},
            'measures': [],
            'simulation_output_report': {},
            'server_directory_cleanup': {}
        }
        workflow_args.update(self.cfg['workflow_generator'].get('args', {}))

        logger.debug('Generating OSW, sim_id={}'.format(sim_id))

        sim_ctl_args = {}

        bld_exist_model_args = {
            'building_id': building_id,
            'sample_weight': self.cfg['baseline']['n_buildings_represented'] / self.n_datapoints
        }
        if 'measures_to_ignore' in workflow_args:
            bld_exist_model_args['measures_to_ignore'] = '|'.join(workflow_args['measures_to_ignore'])
        bld_exist_model_args.update(sim_ctl_args)
        bld_exist_model_args.update(workflow_args['build_existing_model'])

        if 'emissions' in workflow_args:
            emissions = workflow_args['emissions']
            emissions_map = [['emissions_scenario_names', 'scenario_name'],
                             ['emissions_types', 'type'],
                             ['emissions_electricity_folders', 'elec_folder'],
                             ['emissions_natural_gas_values', 'gas_value'],
                             ['emissions_propane_values', 'propane_value'],
                             ['emissions_fuel_oil_values', 'oil_value'],
                             ['emissions_wood_values', 'wood_value']]
            for arg, item in emissions_map:
                bld_exist_model_args[arg] = ','.join([str(s.get(item, '')) for s in emissions])

        if 'utility_bills' in workflow_args:
            utility_bills = workflow_args['utility_bills']
            utility_bills_map = [
                ['utility_bill_scenario_names', 'scenario_name'],
                ['utility_bill_electricity_fixed_charges', 'elec_fixed_charge'],
                ['utility_bill_electricity_marginal_rates', 'elec_marginal_rate'],
                ['utility_bill_natural_gas_fixed_charges', 'gas_fixed_charge'],
                ['utility_bill_natural_gas_marginal_rates', 'gas_marginal_rate'],
                ['utility_bill_propane_fixed_charges', 'propane_fixed_charge'],
                ['utility_bill_propane_marginal_rates', 'propane_marginal_rate'],
                ['utility_bill_fuel_oil_fixed_charges', 'oil_fixed_charge'],
                ['utility_bill_fuel_oil_marginal_rates', 'oil_marginal_rate'],
                ['utility_bill_wood_fixed_charges', 'wood_fixed_charge'],
                ['utility_bill_wood_marginal_rates', 'wood_marginal_rate'],
                ['utility_bill_pv_compensation_types', 'pv_compensation_type'],
                ['utility_bill_pv_net_metering_annual_excess_sellback_rate_types',
                 'pv_net_metering_annual_excess_sellback_rate_type'],
                ['utility_bill_pv_net_metering_annual_excess_sellback_rates',
                 'pv_net_metering_annual_excess_sellback_rate'],
                ['utility_bill_pv_feed_in_tariff_rates', 'pv_feed_in_tariff_rate'],
                ['utility_bill_pv_monthly_grid_connection_fee_units', 'pv_monthly_grid_connection_fee_units'],
                ['utility_bill_pv_monthly_grid_connection_fees', 'pv_monthly_grid_connection_fee']
            ]
            for arg, item in utility_bills_map:
                bld_exist_model_args[arg] = ','.join([str(s.get(item, '')) for s in utility_bills])

        sim_out_rep_args = {
            'timeseries_frequency': 'none',
            'include_timeseries_total_consumptions': False,
            'include_timeseries_fuel_consumptions': False,
            'include_timeseries_end_use_consumptions': True,
            'include_timeseries_emissions': False,
            'include_timeseries_emission_fuels': False,
            'include_timeseries_emission_end_uses': False,
            'include_timeseries_hot_water_uses': False,
            'include_timeseries_total_loads': True,
            'include_timeseries_component_loads': False,
            'include_timeseries_zone_temperatures': False,
            'include_timeseries_airflows': False,
            'include_timeseries_weather': False,
            'add_timeseries_dst_column': True,
            'add_timeseries_utc_column': True
        }
        sim_out_rep_args.update(workflow_args['simulation_output_report'])

        if 'output_variables' in sim_out_rep_args:
            output_variables = sim_out_rep_args['output_variables']
            sim_out_rep_args['user_output_variables'] = ','.join([str(s.get('name')) for s in output_variables])
            sim_out_rep_args.pop('output_variables')

        osw = {
            'id': sim_id,
            'steps': [
                {
                    'measure_dir_name': 'BuildExistingModel',
                    'arguments': bld_exist_model_args
                }
            ],
            'created_at': dt.datetime.now().isoformat(),
            'measure_paths': [
                'measures',
                'resources/hpxml-measures'
            ],
            'run_options': {
                'skip_zip_results': True
            }
        }

        osw['steps'].extend(workflow_args['measures'])

        debug = False
        if 'debug' in workflow_args:
            debug = workflow_args['debug']

        server_dir_cleanup_args = {
          'retain_in_osm': False,
          'retain_in_idf': True,
          'retain_pre_process_idf': False,
          'retain_eplusout_audit': False,
          'retain_eplusout_bnd': False,
          'retain_eplusout_eio': False,
          'retain_eplusout_end': False,
          'retain_eplusout_err': False,
          'retain_eplusout_eso': False,
          'retain_eplusout_mdd': False,
          'retain_eplusout_mtd': False,
          'retain_eplusout_rdd': False,
          'retain_eplusout_shd': False,
          'retain_eplusout_msgpack': False,
          'retain_eplustbl_htm': False,
          'retain_stdout_energyplus': False,
          'retain_stdout_expandobject': False,
          'retain_schedules_csv': True,
          'debug': debug
        }
        server_dir_cleanup_args.update(workflow_args['server_directory_cleanup'])

        osw['steps'].extend([
            {
                'measure_dir_name': 'HPXMLtoOpenStudio',
                'arguments': {
                    'hpxml_path': '../../../run/home.xml',
                    'output_dir': '../../../run',
                    'debug': debug
                }
            },
            {
                'measure_dir_name': 'ReportSimulationOutput',
                'arguments': sim_out_rep_args
            },
            {
                'measure_dir_name': 'ReportHPXMLOutput',
                'arguments': {}
            },
            {
                'measure_dir_name': 'ReportUtilityBills',
                'arguments': {}
            },
            {
                'measure_dir_name': 'UpgradeCosts',
                'arguments': {
                    'debug': debug
                }
            },
            {
                'measure_dir_name': 'ServerDirectoryCleanup',
                'arguments': server_dir_cleanup_args
            }
        ])

        if upgrade_idx is not None:
            measure_d = self.cfg['upgrades'][upgrade_idx]
            apply_upgrade_measure = {
                'measure_dir_name': 'ApplyUpgrade',
                'arguments': {
                    'run_measure': 1
                }
            }
            if 'upgrade_name' in measure_d:
                apply_upgrade_measure['arguments']['upgrade_name'] = measure_d['upgrade_name']
            for opt_num, option in enumerate(measure_d['options'], 1):
                apply_upgrade_measure['arguments']['option_{}'.format(opt_num)] = option['option']
                if 'lifetime' in option:
                    apply_upgrade_measure['arguments']['option_{}_lifetime'.format(opt_num)] = option['lifetime']
                if 'apply_logic' in option:
                    apply_upgrade_measure['arguments']['option_{}_apply_logic'.format(opt_num)] = \
                        self.make_apply_logic_arg(option['apply_logic'])
                for cost_num, cost in enumerate(option.get('costs', []), 1):
                    for arg in ('value', 'multiplier'):
                        if arg not in cost:
                            continue
                        apply_upgrade_measure['arguments']['option_{}_cost_{}_{}'.format(opt_num, cost_num, arg)] = \
                            cost[arg]
            if 'package_apply_logic' in measure_d:
                apply_upgrade_measure['arguments']['package_apply_logic'] = \
                    self.make_apply_logic_arg(measure_d['package_apply_logic'])

            build_existing_model_idx = \
                [x['measure_dir_name'] == 'BuildExistingModel' for x in osw['steps']].index(True)
            osw['steps'].insert(build_existing_model_idx + 1, apply_upgrade_measure)

        if 'reporting_measures' in workflow_args:
            for reporting_measure in workflow_args['reporting_measures']:
                if 'arguments' not in reporting_measure:
                    reporting_measure['arguments'] = {}
                reporting_measure['measure_type'] = 'ReportingMeasure'
                osw['steps'].insert(-1, reporting_measure)  # right before ServerDirectoryCleanup

        return osw
