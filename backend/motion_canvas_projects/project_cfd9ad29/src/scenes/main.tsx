
import {makeScene2D, Rect, Txt, Line, Circle} from '@motion-canvas/2d';
import {createRef, createRefArray, all, sequence, waitFor, easeOutCubic} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
    // Theme colors
    const bgColor = "#0f141e";
    const primaryColor = "#00ff88";
    
    // Set background
    view.fill(bgColor);
    
    // Video dimensions (9:16 for shorts)
    const width = 1080;
    const height = 1920;
    
    // Common elements
    const title = createRef<Txt>();
    const subtitle = createRef<Txt>();
    const underline = createRef<Rect>();
    const card = createRef<Rect>();
    const termText = createRef<Txt>();
    const defText = createRef<Txt>();
    const separator = createRef<Rect>();
    const leftAccent = createRef<Rect>();
    
    const cardWidth = 900;
    const cardHeight = 400;
    const boxWidth = 200;
    
    // Add base elements to view
    view.add(
        <>
            <Txt
                ref={title}
                fontSize={64}
                fontFamily={"Arial"}
                fill={"#ffffff"}
                y={-200}
            />
            <Txt
                ref={subtitle}
                fontSize={28}
                fontFamily={"Arial"}
                fill={"#bbbbbb"}
                y={-100}
                opacity={0}
            />
            <Rect
                ref={underline}
                width={0}
                height={5}
                fill={primaryColor}
                y={-140}
            />
            <Rect
                ref={card}
                width={cardWidth}
                height={cardHeight}
                fill={"#192332"}
                radius={10}
                opacity={0}
            >
                <Rect
                    ref={leftAccent}
                    width={8}
                    height={0}
                    fill={primaryColor}
                    x={-cardWidth/2 + 4}
                />
                <Txt
                    ref={termText}
                    fontSize={40}
                    fontFamily={"Arial"}
                    fill={"white"}
                    y={-80}
                    x={-cardWidth/2 + 150}
                />
                <Rect
                    ref={separator}
                    width={0}
                    height={2}
                    fill={primaryColor}
                    y={-30}
                    opacity={0.5}
                />
                <Txt
                    ref={defText}
                    fontSize={24}
                    fontFamily={"Arial"}
                    fill={"#dddddd"}
                    y={50}
                    width={cardWidth - 80}
                    textWrap={true}
                />
            </Rect>
        </>
    );
    
    // Scene animations
    // Scene 1: title

// Title Scene
yield* sequence(0.1,
    title().text("EVER WAITED IN LINE?", 0.5),
    title().fill("#00ff88", 0.3),
);

yield* all(
    title().scale(1.1, 0.3).to(1, 0.2),
    underline().width(400, 0.5),
);

if ("What if I told you computers wait in line too? And they follow the same rules as your school cafeteria!") {
    yield* subtitle().text("What if I told you computers wait in line too? And they follow the same rules as", 0.4);
    yield* subtitle().opacity(1, 0.3);
}

yield* waitFor(5.72);
yield* all(
    title().opacity(0, 0.3),
    subtitle().opacity(0, 0.3),
    underline().width(0, 0.3),
);

// Scene 2: definition

// Definition Scene
yield* sequence(0.1,
    card().opacity(1, 0.3),
    card().scale(0.9, 0).to(1, 0.4),
);

yield* sequence(0.2,
    termText().text("QUEUE = LINE", 0.4),
    separator().width(cardWidth - 60, 0.3),
    defText().text("A queue is just a fancy word for a line. First in, first out - just like when you're waiting for pizza!", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor(5.92);

yield* all(
    card().scale(1.05, 0.2).to(0.9, 0.2),
    card().opacity(0, 0.3),
);

// Scene 3: explanation

// Definition Scene
yield* sequence(0.1,
    card().opacity(1, 0.3),
    card().scale(0.9, 0).to(1, 0.4),
);

yield* sequence(0.2,
    termText().text("WHY IT MATTERS", 0.4),
    separator().width(cardWidth - 60, 0.3),
    defText().text("You use queues every day! Printing documents, downloading files, even when you're waiting for your turn in a game.", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor(5.99);

yield* all(
    card().scale(1.05, 0.2).to(0.9, 0.2),
    card().opacity(0, 0.3),
);

// Scene 4: process

// Process Flow Scene
const steps = ["Think of it like this: you join the line at the ba"];
const stepBoxes = createRefArray<Rect>();
const stepTexts = createRefArray<Txt>();
const stepAccents = createRefArray<Rect>();
const arrows = createRefArray<Line>();

yield* title().text("HOW IT WORKS", 0.3);

// Show subtitle (narration) at bottom
if ("Think of it like this: you join the line at the back, and the person at the front gets ser") {
    yield* subtitle().text("Think of it like this: you join the line at the back, and the person at the front gets ser", 0.4);
    yield* subtitle().opacity(1, 0.3);
}

// Add layout to view
view.add(
    <>
        {steps.map((step, i) => (
            <>
                <Rect
                    ref={stepBoxes[i]}
                    width={600}
                    height={100}
                    fill={"#192332"}
                    radius={10}
                    opacity={0}
                    y={-100 + i * 150} // Vertical layout
                >
                     <Rect
                        ref={stepAccents[i]}
                        width={0}
                        height={100}
                        fill={i % 2 === 0 ? "#00ff88" : "#40c4ff"}
                        x={-300} // Left edge
                    />
                    <Txt
                        ref={stepTexts[i]}
                        text={step}
                        fontSize={32}
                        fontFamily={"Arial"}
                        fill={"#ffffff"}
                    />
                </Rect>
                {i < steps.length - 1 && (
                    <Line
                        ref={arrows[i]}
                        points={{[[0, -50 + i * 150], [0, -100 + (i + 1) * 150]]}}
                        stroke={"#ffffff"}
                        lineWidth={4}
                        endArrow={true}
                        opacity={0}
                    />
                )}
            </>
        ))}
    </>
);


    // Step 1
    yield* sequence(0.1,
        stepBoxes[0].opacity(1, 0.3),
        stepBoxes[0].scale(0.8, 0).to(1, 0.3),
        stepTexts[0].text("Think of it like this: you join the line at the ba", 0.3),
        stepAccents[0].width(boxWidth, 0.2),
    );
    
    yield* waitFor(0.5);


yield* waitFor(4.97);

// Scene 5: example

// Definition Scene
yield* sequence(0.1,
    card().opacity(1, 0.3),
    card().scale(0.9, 0).to(1, 0.4),
);

yield* sequence(0.2,
    termText().text("REAL LIFE EXAMPLE", 0.4),
    separator().width(cardWidth - 60, 0.3),
    defText().text("Like when you're waiting for your turn on the playground swing. First come, first swing!", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor(4.31);

yield* all(
    card().scale(1.05, 0.2).to(0.9, 0.2),
    card().opacity(0, 0.3),
);

// Scene 6: summary

// Summary Scene
yield* title().text("✅ REMEMBER THIS", 0.4);

const checkmarks = createRefArray<Txt>();
const pointTexts = createRefArray<Txt>();
const pointBgs = createRefArray<Rect>();


    yield* sequence(0.1,
        checkmarks[0].opacity(1, 0.2),
        checkmarks[0].scale(0, 0).to(1, 0.3),
        pointTexts[0].text("Queue = Line", 0.3),
        pointBgs[0].opacity(1, 0.2),
    );
    yield* waitFor(0.4);

    yield* sequence(0.1,
        checkmarks[1].opacity(1, 0.2),
        checkmarks[1].scale(0, 0).to(1, 0.3),
        pointTexts[1].text("First in, first out", 0.3),
        pointBgs[1].opacity(1, 0.2),
    );
    yield* waitFor(0.4);

    yield* sequence(0.1,
        checkmarks[2].opacity(1, 0.2),
        checkmarks[2].scale(0, 0).to(1, 0.3),
        pointTexts[2].text("No cutting!", 0.3),
        pointBgs[2].opacity(1, 0.2),
    );
    yield* waitFor(0.4);


yield* waitFor(6.06);

    
    // End
    yield* waitFor(0.5);
});
