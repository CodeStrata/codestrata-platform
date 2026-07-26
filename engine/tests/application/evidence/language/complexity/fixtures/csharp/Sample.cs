using System;
using System.Collections.Generic;

namespace Sample.Complexity;

public sealed class Calculator
{
    public int Add(int left, int right)
    {
        return left + right;
    }

    public int ComplexScore(IReadOnlyList<int> values)
    {
        var score = 0;
        foreach (var value in values)
        {
            if (value > 10 && value < 100)
            {
                score += value;
            }
            else if (value < 0)
            {
                score -= 1;
            }
            else
            {
                try
                {
                    score += value % 2 == 0 ? 2 : 1;
                }
                catch (Exception)
                {
                    score = 0;
                }
            }
        }
        return score;
    }
}
