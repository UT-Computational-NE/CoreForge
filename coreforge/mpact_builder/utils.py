from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Callable, Dict, Any

import numpy as np
import mpactpy

from coreforge import geometry_elements

def build_elements(elements:        List[geometry_elements.GeometryElement],
                   worker_function: Callable[..., mpactpy.Core],
                   num_processes:   int,
                   *worker_args:    Any
    ) -> Dict[geometry_elements.GeometryElement, mpactpy.Core]:
    """Build geometry elements in parallel using chunked distribution.

    Parameters
    ----------
    elements : List[geometry_elements.GeometryElement]
        List of geometry elements to process
    worker_function : Callable
        Function to process each chunk. Should accept (chunk, *worker_args)
        and return a list of results
    num_processes : int
        Maximum number of processes to use
    *worker_args : Any
        Additional arguments to pass to the worker function

    Returns
    -------
    Dict[geometry_elements.GeometryElement, mpactpy.Core]
        Mapping from geometry element to built mpact geometry.
    """
    if not elements:
        return {}

    # Determine the number of chunks and create them
    num_chunks    = min(num_processes, len(elements))
    chunk_indices = np.array_split(np.arange(len(elements)), num_chunks)
    work_chunks = [[elements[i] for i in indices] for indices in chunk_indices]

    results = {}
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        future_to_chunk_index = {
            executor.submit(worker_function, chunk, *worker_args): i
            for i, chunk in enumerate(work_chunks)
        }
        chunk_results = [None] * len(work_chunks)
        for future in as_completed(future_to_chunk_index):
            chunk_index = future_to_chunk_index[future]
            chunk_results[chunk_index] = future.result()

        for chunk_result in chunk_results:
            for item, result in chunk_result:
                results[item] = result

    return results
