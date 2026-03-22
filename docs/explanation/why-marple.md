# Why MARPLE Exists

For many years now I have used Dyalog APL for personal projects, and I love it. It's fast, solid and well-supported. It's also allowed me to learn from some very smart people. But for me, it has three disadvantages: I can't extend it, it does not yet use an available GPU and it uses *floating* nested arrays.

Ken Iverson preferred the *grounded* approach for nested arrays, and so do I. While I have not implemented nested arrays in MARPLE yet, I plan to do so and I will follow the approach described by Iverson in his **Dictionary of APL**.

I've also made MARPLE easy to extend. It is implemented in Python, and there is a simple mechanism that allows you to add new language features in Python and then use i-beams to turn them into functions available to the APL developer.

Will it make use of GPUs? I hope so, and I expect to demonstrate that soon. _Watch this space!_

