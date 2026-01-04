
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
    title().text("STACKS EVERYWHERE!", 0.5),
    title().fill("#00ff88", 0.3),
);

yield* all(
    title().scale(1.1, 0.3).to(1, 0.2),
    underline().width(400, 0.5),
);

if ("Ever wondered how your undo button remembers everything? It's like magic... but it's actually a stack!") {
    yield* subtitle().text("Ever wondered how your undo button remembers everything? It'", 0.4);
    yield* subtitle().opacity(1, 0.3);
}

yield* waitFor(5.8);
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
    termText().text("WHAT'S A STACK?", 0.4),
    separator().width(cardWidth - 60, 0.3),
    defText().text("A stack is like a tower of pancakes. You can only add or take from the top!", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor(4.29);

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
    defText().text("You use stacks every time you hit 'undo' or when your browser remembers pages you visited.", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor(4.12);

yield* all(
    card().scale(1.05, 0.2).to(0.9, 0.2),
    card().opacity(0, 0.3),
);

// Scene 4: diagram

// Definition Scene
yield* sequence(0.1,
    card().opacity(1, 0.3),
    card().scale(0.9, 0).to(1, 0.4),
);

yield* sequence(0.2,
    termText().text("HOW IT WORKS", 0.4),
    separator().width(cardWidth - 60, 0.3),
    defText().text("Imagine adding plates to a pile. The last one you put on is the first one you take off!", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor(4.74);

yield* all(
    card().scale(1.05, 0.2).to(0.9, 0.2),
    card().opacity(0, 0.3),
);

// Scene 5: process

// Process Flow Scene
const steps = ["Two simple rules: Last In, First Out (LI", "Push to add, pop to remove"];
const stepBoxes = createRefArray<Rect>();
const stepTexts = createRefArray<Txt>();
const stepAccents = createRefArray<Rect>();
const arrows = createRefArray<Line>();

yield* title().text("STACK RULES", 0.3);


    // Step 1
    yield* sequence(0.1,
        stepBoxes[0].opacity(1, 0.3),
        stepBoxes[0].scale(0.8, 0).to(1, 0.3),
        stepTexts[0].text("Two simple rules: Last In, First Out (LI", 0.3),
        stepAccents[0].width(boxWidth, 0.2),
    );
    yield* arrows[0].opacity(1, 0.2);
    yield* waitFor(0.5);

    // Step 2
    yield* sequence(0.1,
        stepBoxes[1].opacity(1, 0.3),
        stepBoxes[1].scale(0.8, 0).to(1, 0.3),
        stepTexts[1].text("Push to add, pop to remove", 0.3),
        stepAccents[1].width(boxWidth, 0.2),
    );
    
    yield* waitFor(0.5);


yield* waitFor(5.09);

// Scene 6: example

// Definition Scene
yield* sequence(0.1,
    card().opacity(1, 0.3),
    card().scale(0.9, 0).to(1, 0.4),
);

yield* sequence(0.2,
    termText().text("REAL LIFE", 0.4),
    separator().width(cardWidth - 60, 0.3),
    defText().text("Like when you stack books. The last book you put on top is the first one you grab!", 0.5),
);

yield* leftAccent().height(cardHeight, 0.3);
yield* waitFor(4.1);

yield* all(
    card().scale(1.05, 0.2).to(0.9, 0.2),
    card().opacity(0, 0.3),
);

// Scene 7: summary

// Summary Scene
yield* title().text("✅ REMEMBER THIS", 0.4);

const checkmarks = createRefArray<Txt>();
const pointTexts = createRefArray<Txt>();
const pointBgs = createRefArray<Rect>();


    yield* sequence(0.1,
        checkmarks[0].opacity(1, 0.2),
        checkmarks[0].scale(0, 0).to(1, 0.3),
        pointTexts[0].text("Stacks are simple: LIFO, push, pop", 0.3),
        pointBgs[0].opacity(1, 0.2),
    );
    yield* waitFor(0.4);

    yield* sequence(0.1,
        checkmarks[1].opacity(1, 0.2),
        checkmarks[1].scale(0, 0).to(1, 0.3),
        pointTexts[1].text("Now you know how your undo button works", 0.3),
        pointBgs[1].opacity(1, 0.2),
    );
    yield* waitFor(0.4);


yield* waitFor(5.5);

    
    // End
    yield* waitFor(0.5);
});
