float PerlinNoise(float value, float frequency, int octaves, int seed)
{
    float noiseSum = 0.0;
    float amplitude = 0.5;
    for (int octave = 0; octave < octaves - 1; octave++)
    {
        float v = value * frequency + float(seed) * 12.468;
        float a = Noise(int(v), seed);
        float b = Noise(int(v) + 1, seed);
        float t = Fade(v - floor(v));
        noiseSum += lerp(a, b, t) * amplitude;
        frequency *= 2;
        amplitude *= 0.5;
    }
    return noiseSum;
}

float Noise(int x, int seed)
{
    int n = x + seed * 137;
    n = n << 13 ^ n;
    return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0);
}

float Fade(float t)
{
    return t * t * t * (t * (t * 6 - 15) + 10);
}


result = float3(
    PerlinNoise(value * -1.0, frequency, octaves, seed),
    PerlinNoise(value + 465.321, frequency, octaves, seed),
    PerlinNoise(value, frequency, octaves, seed),
);