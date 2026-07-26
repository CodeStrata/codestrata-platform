<?php

namespace Demo;

class Sample
{
    private int $seed;

    public function __construct(int $seed)
    {
        $this->seed = $seed;
    }

    public function compute(int $a, int $b, int $c): int
    {
        $total = 0;
        if ($a > 0 && $b > 0) {
            for ($i = 0; $i < $a; $i++) {
                if ($i % 2 === 0) {
                    $total += $i;
                } else {
                    while ($c > 0) {
                        $c--;
                        $total++;
                    }
                }
            }
        } elseif ($a < 0 || $b < 0) {
            $total = -1;
        } else {
            $total = $c > 0 ? $a + $b : 0;
        }
        try {
            if ($total < -1) {
                throw new \RuntimeException('bad');
            }
        } catch (\RuntimeException $ex) {
            return 0;
        }
        return $total;
    }

    public function emptyMethod(): void
    {
    }
}

function top_level_helper(int $value): int
{
    if ($value > 0) {
        return $value;
    }
    return 0;
}
