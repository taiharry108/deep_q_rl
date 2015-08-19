#! /usr/bin/env python
"""This script handles reading command line arguments and starting the
training process.  It shouldn't be executed directly; it is used by
run_nips.py or run_nature.py.

"""
from inspect import ismethod
import os
import argparse
import logging
import ale_python_interface
import numpy as np
import theano
import ale_experiment


def process_args(args, defaults, description):
    """
    Handle the command line.

    args     - list of command line arguments (not including executable name)
    defaults - a name space with variables corresponding to each of
               the required default command line values.
    description - a string to display at the top of the help message.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-r', '--rom', dest="rom", default=defaults.ROM,
                        help='ROM to run (default: %(default)s)')
    parser.add_argument('-e', '--epochs', dest="epochs", type=int,
                        default=defaults.EPOCHS,
                        help='Number of training epochs (default: %(default)s)')
    parser.add_argument('-s', '--steps-per-epoch', dest="steps_per_epoch",
                        type=int, default=defaults.STEPS_PER_EPOCH,
                        help='Number of steps per epoch (default: %(default)s)')
    parser.add_argument('-t', '--test-length', dest="steps_per_test",
                        type=int, default=defaults.STEPS_PER_TEST,
                        help='Number of steps per test (default: %(default)s)')
    parser.add_argument('--display-screen', dest="display_screen",
                        action='store_true', default=False,
                        help='Show the game screen.')
    parser.add_argument('--experiment-prefix', dest="experiment_prefix",
                        default=None,
                        help='Experiment name prefix '
                             '(default is the name of the game)')
    parser.add_argument('--frame-skip', dest="frame_skip",
                        default=defaults.FRAME_SKIP, type=int,
                        help='Every how many frames to process '
                             '(default: %(default)s)')
    parser.add_argument('--repeat-action-probability',
                        dest="repeat_action_probability",
                        default=defaults.REPEAT_ACTION_PROBABILITY, type=float,
                        help=('Probability that action choice will be ' +
                              'ignored (default: %(default)s)'))

    parser.add_argument('--update-rule', dest="update_rule",
                        type=str, default=defaults.UPDATE_RULE,
                        help=('deepmind_rmsprop|rmsprop|sgd ' +
                              '(default: %(default)s)'))
    parser.add_argument('--batch-accumulator', dest="batch_accumulator",
                        type=str, default=defaults.BATCH_ACCUMULATOR,
                        help='sum|mean (default: %(default)s)')
    parser.add_argument('--learning-rate', dest="learning_rate",
                        type=float, default=defaults.LEARNING_RATE,
                        help='Learning rate (default: %(default)s)')
    parser.add_argument('--rms-decay', dest="rms_decay",
                        type=float, default=defaults.RMS_DECAY,
                        help='Decay rate for rms_prop (default: %(default)s)')
    parser.add_argument('--rms-epsilon', dest="rms_epsilon",
                        type=float, default=defaults.RMS_EPSILON,
                        help='Denominator epsilson for rms_prop ' +
                             '(default: %(default)s)')
    parser.add_argument('--momentum', type=float, default=defaults.MOMENTUM,
                        help=('Momentum term for Nesterov momentum. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--clip-delta', dest="clip_delta", type=float,
                        default=defaults.CLIP_DELTA,
                        help=('Max absolute value for Q-update delta value. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--discount', type=float, default=defaults.DISCOUNT,
                        help='Discount rate')
    parser.add_argument('--epsilon-start', dest="epsilon_start",
                        type=float, default=defaults.EPSILON_START,
                        help=('Starting value for epsilon. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--epsilon-min', dest="epsilon_min",
                        type=float, default=defaults.EPSILON_MIN,
                        help='Minimum epsilon. (default: %(default)s)')
    parser.add_argument('--epsilon-decay', dest="epsilon_decay",
                        type=float, default=defaults.EPSILON_DECAY,
                        help=('Number of steps to minimum epsilon. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--phi-length', dest="phi_length",
                        type=int, default=defaults.PHI_LENGTH,
                        help=('Number of recent frames used to represent ' +
                              'state. (default: %(default)s)'))
    parser.add_argument('--max-history', dest="replay_memory_size",
                        type=int, default=defaults.REPLAY_MEMORY_SIZE,
                        help=('Maximum number of steps stored in replay ' +
                              'memory. (default: %(default)s)'))
    parser.add_argument('--batch-size', dest="batch_size",
                        type=int, default=defaults.BATCH_SIZE,
                        help='Batch size. (default: %(default)s)')
    parser.add_argument('--network-type', dest="network_type",
                        type=str, default=defaults.NETWORK_TYPE,
                        help=('nips_cuda|nips_dnn|nature_cuda|nature_dnn' +
                              '|linear (default: %(default)s)'))
    parser.add_argument('--freeze-interval', dest="freeze_interval",
                        type=int, default=defaults.FREEZE_INTERVAL,
                        help=('Interval between target freezes. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--update-frequency', dest="update_frequency",
                        type=int, default=defaults.UPDATE_FREQUENCY,
                        help=('Number of actions before each SGD update. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--replay-start-size', dest="replay_start_size",
                        type=int, default=defaults.REPLAY_START_SIZE,
                        help=('Number of random steps before training. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--resize-method', dest="resize_method",
                        type=str, default=defaults.RESIZE_METHOD,
                        help=('crop|scale (default: %(default)s)'))
    parser.add_argument('--nn-file', dest="nn_file", type=str, default=None,
                        help='Pickle file containing trained net.')
    parser.add_argument('--death-ends-episode', dest="death_ends_episode",
                        type=str, default=defaults.DEATH_ENDS_EPISODE,
                        help=('true|false (default: %(default)s)'))
    parser.add_argument('--max-start-nullops', dest="max_start_nullops",
                        type=int, default=defaults.MAX_START_NULLOPS,
                        help=('Maximum number of null-ops at the start ' +
                              'of games. (default: %(default)s)'))
    parser.add_argument('--deterministic', dest="deterministic",
                        type=bool, default=defaults.DETERMINISTIC,
                        help=('Whether to use deterministic parameters ' +
                              'for learning. (default: %(default)s)'))
    parser.add_argument('--cudnn_deterministic', dest="cudnn_deterministic",
                        type=bool, default=defaults.CUDNN_DETERMINISTIC,
                        help=('Whether to use deterministic backprop. ' +
                              '(default: %(default)s)'))

    params = parser.parse_args(args)
    if params.experiment_prefix is None:
        name = os.path.splitext(os.path.basename(params.rom))[0]
        params.experiment_prefix = name

    if params.death_ends_episode == 'true':
        params.death_ends_episode = True
    elif params.death_ends_episode == 'false':
        params.death_ends_episode = False
    else:
        raise ValueError("--death-ends-episode must be true or false")

    if params.freeze_interval > 0:
        # This addresses an inconsistency between the Nature paper and
        # the Deepmind code.  The paper states that the target network
        # update frequency is "measured in the number of parameter
        # updates".  In the code it is actually measured in the number
        # of action choices.
        params.freeze_interval = (params.freeze_interval //
                                      params.update_frequency)

    # Get default parameters and apply to the parameters namespace when missing
    defaults_dict = dict(
        (k.lower(), v) for k, v in defaults.__dict__.iteritems()
        if not ismethod(v) and not k.startswith('__')
    )

    for k in defaults_dict:
        if not hasattr(params, k):
            setattr(params, k, defaults_dict[k])

    return params


def launch(args, defaults, description):
    """
    Execute a complete training run.
    """

    logging.basicConfig(level=logging.INFO)
    params = process_args(args, defaults, description)

    if params.rom.endswith('.bin'):
        rom = params.rom
    else:
        rom = "%s.bin" % params.rom
    full_rom_path = os.path.join(defaults.BASE_ROM_PATH, rom)

    if params.deterministic:
        params.rng = np.random.RandomState(123456)
    else:
        params.rng = np.random.RandomState()

    if params.cudnn_deterministic:
        theano.config.dnn.conv.algo_bwd = 'deterministic'

    ale = ale_python_interface.ALEInterface()
    ale.setInt('random_seed', params.rng.randint(1000))

    if params.display_screen:
        import sys
        if sys.platform == 'darwin':
            import pygame
            pygame.init()
            ale.setBool('sound', False) # Sound doesn't work on OSX

    ale.setBool('display_screen', params.display_screen)
    ale.setFloat('repeat_action_probability',
                 params.repeat_action_probability)

    ale.loadROM(full_rom_path)

    if params.agent_type is None:
        raise Exception("The agent type has not been specified")

    agent = params.agent_type(params)

    experiment = ale_experiment.ALEExperiment(
        ale=ale,
        agent=agent,
        resized_width=params.resized_width,
        resized_height=params.resized_height,
        resize_method=params.resize_method,
        num_epochs=params.epochs,
        epoch_length=params.steps_per_epoch,
        test_length=params.steps_per_test,
        frame_skip=params.frame_skip,
        death_ends_episode=params.death_ends_episode,
        max_start_nullops=params.max_start_nullops,
        rng=params.rng)

    experiment.run()


if __name__ == '__main__':
    pass
