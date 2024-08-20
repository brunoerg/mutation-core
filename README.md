# Mutation Core

**A mutation testing tool for Bitcoin Core**. 

"Mutation testing (or mutation analysis or program mutation) is used to design new software tests and evaluate the quality of existing software tests. Mutation testing involves modifying a program in small ways.[1] Each mutated version is called a mutant and tests detect and reject mutants by causing the behaviour of the original version to differ from the mutant. This is called killing the mutant. Test suites are measured by the percentage of mutants that they kill." (Wikipedia)

## Features

- Allows generating mutants only for the code touched or added in a specific branch (useful to test PRs) and avoid spending time by generating mutants for files from bench/test/doc/etc folders.
- Allows generating mutants using only some security-based mutation operators. This might be good for testing fuzzing.

    - e.g:
    ```diff
        @@ -630,7 +630,7 @@ static void ApproximateBestSubset(FastRandomContext& insecure_rand, const std::v
                    {
                        nTotal += groups[i].GetSelectionAmount();
                        selected_coins_weight += groups[i].m_weight;
    -                   vfIncluded[i] = true;
    +                   vfIncluded[i + 100] = true;
                        if (nTotal >= nTargetValue && selected_coins_weight <= max_selection_weight) {
                            fReachedTarget = true;
                            // If the total is between nTargetValue and nBest, it's our new best
    ```
    ```diff
        @@ -560,7 +560,7 @@ util::Result<SelectionResult> SelectCoinsSRD(const std::vector<OutputGroup>& utx
    
            // Add group to selection
            heap.push(group);
    -        selected_eff_value += group.GetSelectionAmount();
    +        selected_eff_value += group.GetSelectionAmount() + std::numeric_limits<CAmount>::max();
            weight += group.m_weight;
    
            // If the selection weight exceeds the maximum allowed size, remove the least valuable inputs until we
    ```
    ```diff
        @@ -4194,7 +4194,7 @@ static bool ContextualCheckBlockHeader(const CBlockHeader& block, BlockValidatio
        }
    
        // Check timestamp against prev
    -    if (block.GetBlockTime() <= pindexPrev->GetMedianTimePast())
    +    if (block.GetBlockTime() <= std::numeric_limits<int64_t>::max())
            return state.Invalid(BlockValidationResult::BLOCK_INVALID_HEADER, "time-too-old", "block's timestamp is too early");
    
        // Testnet4 only: Check timestamp against prev for difficulty-adjustment
    ```
- Avoids creating useless mutants. (e.g. by skipping comments, `LogPrintf` statements...).
- Allows generating only one mutant per line of code (might be useful for CI/CD).
- Allows creating mutations in the functional tests.

...and, of course, there are some specific mutation operators designed for Bitcoin Core.

## How to use

Generate mutants for a specific file:
```sh
./mutation-core.py mutate -f=path/to/file
```

Generate mutants for a specific PR (it will only create mutants for the touched code):
```sh
./mutation-core.py mutate -p=PR_NUMBER
```

Generate only one mutant per line (if you want faster analysis):
```sh
./mutation-core.py mutate -p=PR_NUMBER --one_mutant=1
```

If you do not specify either a file or PR number, it will create mutants for the touched code by the current branch you are checked out. If the specified file is a Python one, it will create mutants considering it is a functional test.

The `mutate` command will create a folder with all mutants. To test them you can use:
```sh
./mutation-core.py analyze -f=path/to/folder -c="command to test each mutant"
```
e.g.
```sh
./mutation-core.py analyze -f=path/to/folder -c="make && ./test/functional/bla.py"
```

## Mutating functional tests

Does it make sense? Yes! See: https://github.com/trailofbits/necessist/blob/master/docs/Necessist%20Mutation%202024.pdf

Of course, this is much simpler than necessist and focused on Bitcoin Core, but mutating tests really makes sense. 
By removing some statements and method calls, we can check whether the test passes and identify buggy tests. In our case, we 
will not touch any `wait_for`, `wait_until`, `send_and_ping`, `assert_*` and other verifications.

See an example of the usage of this tool for `test/functional/p2p_compactblocks.py`.

```bash
./mutation-core.py mutate -f="./test/functional/p2p_compactblocks.py"
```
```bash
./mutation-core.py analyze -f="muts" -c="./test/functional/p2p_compactblocks.py"
```

See some of the surviving mutants:

```diff
--- a/./test/functional/p2p_compactblocks.py
+++ b/muts/p2p_compactblocks.mutant.205.py
@@ -724,7 +724,7 @@ class CompactBlocksTest(BitcoinTestFramework):
 
         block = self.build_block_with_transactions(node, utxo, 5)
         del block.vtx[3]
-        block.hashMerkleRoot = block.calc_merkle_root()
         # Drop the coinbase witness but include the witness commitment.
         add_witness_commitment(block)
         block.vtx[0].wit.vtxinwit = []

```

```diff
--- a/./test/functional/p2p_compactblocks.py
+++ b/muts/p2p_compactblocks.mutant.103.py
@@ -479,7 +479,7 @@ class CompactBlocksTest(BitcoinTestFramework):
         # Now try giving one transaction ahead of time.
         utxo = self.utxos.pop(0)
         block = self.build_block_with_transactions(node, utxo, 5)
-        self.utxos.append([block.vtx[-1].sha256, 0, block.vtx[-1].vout[0].nValue])
         test_node.send_and_ping(msg_tx(block.vtx[1]))
         assert block.vtx[1].hash in node.getrawmempool()
 
```

```diff
--- a/./test/functional/p2p_compactblocks.py
+++ b/muts/p2p_compactblocks.mutant.126.py
@@ -580,7 +580,7 @@ class CompactBlocksTest(BitcoinTestFramework):
             msg = msg_getblocktxn()
             msg.block_txn_request = BlockTransactionsRequest(int(block_hash, 16), [])
             num_to_request = random.randint(1, len(block.vtx))
-            msg.block_txn_request.from_absolute(sorted(random.sample(range(len(block.vtx)), num_to_request)))
             test_node.send_message(msg)
             test_node.wait_until(lambda: "blocktxn" in test_node.last_message, timeout=10)
```
