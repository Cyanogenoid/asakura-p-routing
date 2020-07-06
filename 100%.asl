state("AssaCrip_en")
{
    int Floor: "AssaCrip_en.exe", 0x1D9AFC;
    int ScreenType: "AssaCrip_en.exe", 0x1D9BB0;
    int CreditScreen: "AssaCrip_en.exe", 0x1DAC24;
}

init
{
    current.Splits = new int[]
    {
        // area 1
        10,
        // slime
        11,
        // area 2
        25,
        // wisp
        26,
        // area 3
        40,
        // witches
        41,
        // area 4
        55,
        // butterfly
        56,
        // area 5
        70,
        // balloon
        71,
        // area 6
        85,
        // dragon
        98,
        // area 7
        76,
        // 76-72, 41-34 check flag
        28,
        // 28-30b, 28-30, 76-79 blast guard
        15,
        // 15-22, 34-38, 34-33, 64-63 stability pendant
        4,
        // 4-1, 41-57, 15-8, 56-58 nothing
        28,
        // 28-26, 64-68, 98-94 earth guardian
        4,
        // 4-7, 98-91, 41-44 eternal candle, 98-
        100,
        // moon and sun
    };
}

start
{
    // ensure that two frames satisfy condition
    // otherwise continuing a save can accidentally start a run
    if (current.Floor == 0 && current.ScreenType == 1 &&
            old.Floor == 0 &&     old.ScreenType == 1)
    {
        // start at the first split
        current.SplitIndex = 0;
        return true;
    }
    return false;
}

split
{
    int floor = current.Floor + 1;

    // normal splits
    if (current.Floor != old.Floor && floor == current.Splits[current.SplitIndex])
    {
        current.SplitIndex++;
        return true;
    }

    // last split
    if (floor == 100 && current.CreditScreen == 10)
    {
        return true;
    }

    return false;
}
