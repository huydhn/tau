# Copyright (c) Meta Platforms, Inc. and affiliates
from pippy import annotate_split_points, PipeSplitWrapper


def add_split_points(t5, xxcoders_per_rank):
    assert t5.config.num_layers == t5.config.num_decoder_layers
    assert (
        t5.config.num_layers + t5.config.num_decoder_layers
    ) % xxcoders_per_rank == 0
    encoders_per_rank = xxcoders_per_rank
    for i in range(
        0, (t5.config.num_layers + encoders_per_rank - 1) // encoders_per_rank
    ):
        annotate_split_points(
            t5,
            {
                f"encoder.block.{i * encoders_per_rank}": PipeSplitWrapper.SplitPoint.BEGINNING
            },
        )
    decoders_per_rank = xxcoders_per_rank
    for i in range(
        0,
        (t5.config.num_decoder_layers + decoders_per_rank - 1)
        // decoders_per_rank,
    ):
        annotate_split_points(
            t5,
            {
                f"decoder.block.{i * decoders_per_rank}": PipeSplitWrapper.SplitPoint.BEGINNING
            },
        )
    annotate_split_points(
        t5, {"lm_head": PipeSplitWrapper.SplitPoint.BEGINNING}
    )


def wrap(model, training_args, pp_ranks):
    emb_head = 2  # encoder embeddings + decoder embeddings
    master_enc_emb_dec_emb = training_args.exclude_master + emb_head
    num_of_ranks_for_xxcoders = len(pp_ranks) - master_enc_emb_dec_emb
    xxcoders = model.config.num_layers + model.config.num_decoder_layers
    xxcoders_per_rank = (
        xxcoders + num_of_ranks_for_xxcoders - 1
    ) // num_of_ranks_for_xxcoders
    # print(f"xxcoders_per_rank = {xxcoders_per_rank}")
    number_of_workers = emb_head + xxcoders // xxcoders_per_rank
    # print(f"number_of_workers = {number_of_workers}")
    all_worker_ranks = pp_ranks[
        training_args.exclude_master : training_args.exclude_master
        + number_of_workers
    ]
    add_split_points(model, xxcoders_per_rank)
