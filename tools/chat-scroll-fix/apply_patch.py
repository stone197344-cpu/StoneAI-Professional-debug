#!/usr/bin/env python3
"""
Chat scroll fix for StoneAI Professional (com.leestone.stoneai).

Problem (as reported):
    While the model is streaming a reply, the chat list is force-scrolled to the
    bottom on every token, so you cannot scroll/read anything until generation
    finishes.

Why it happens (decompiled from the shipped APK):
    ChatScreen.kt does

        LaunchedEffect(state.messages.size, state.messages.lastOrNull()?.content) {
            if (state.messages.isNotEmpty()) {
                listState.animateScrollToItem(state.messages.lastIndex)
            }
        }

    The key includes the *content* of the last message, so the effect is
    restarted for every streamed token, and each restart kicks off a new
    animateScrollToItem(lastIndex) that drags the list back to the bottom -
    cancelling whatever the user is doing.

Fix:
    Only auto-follow while the list is already scrolled to the bottom.
    The "was the list at the bottom?" flag is read at *composition* time
    (before the new token's content is laid out), so a list that is mid-stream
    while pinned at the bottom keeps following, while a list the user scrolled
    away from is left alone. The scroll itself is switched from
    animateScrollToItem to scrollToItem (instant) because the animation is
    restarted every token and never gets to settle.

    Decompiled equivalent of the patched Kotlin:

        val atBottom = !listState.canScrollForward      // read during composition
        LaunchedEffect(state.messages.size, state.messages.lastOrNull()?.content) {
            if (state.messages.isNotEmpty() && atBottom) {
                listState.scrollToItem(state.messages.lastIndex)
            }
        }

This script rewrites an apktool-decoded smali tree:

    <project>/smali_classes3/com/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1.smali
    <project>/smali_classes3/com/leestone/stoneai/ui/ChatScreenKt.smali
    <project>/smali_classes3/com/leestone/stoneai/ui/ChatScrollSupport.smali   (new)

Usage:
    python3 apply_patch.py /path/to/decoded-project
"""

import os
import sys

UI_DIR = os.path.join("smali_classes3", "com", "leestone", "stoneai", "ui")
EFFECT = os.path.join(UI_DIR, "ChatScreenKt$ChatScreen$1$1.smali")
SCREEN = os.path.join(UI_DIR, "ChatScreenKt.smali")
SUPPORT = os.path.join(UI_DIR, "ChatScrollSupport.smali")

LAMBDA = "Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;"


def sub_once(text, old, new, what, path):
    if text.count(old) != 1:
        raise SystemExit(
            "ERROR: %s: expected exactly 1 occurrence of %r in %s (found %d)"
            % (what, old.strip()[:80], path, text.count(old))
        )
    return text.replace(old, new)


# --------------------------------------------------------------------------
# 1. ChatScreenKt$ChatScreen$1$1 (the LaunchedEffect lambda)
# --------------------------------------------------------------------------

def patch_effect(path):
    src = open(path, encoding="utf-8").read()

    # 1a. new synthetic field that carries the composition-time "at bottom" flag
    src = sub_once(
        src,
        ".field final synthetic $state:Lcom/leestone/stoneai/data/StudioUiState;\n"
        "\n"
        ".field label:I\n",
        ".field final synthetic $state:Lcom/leestone/stoneai/data/StudioUiState;\n"
        "\n"
        ".field final synthetic $atBottom:Z\n"
        "\n"
        ".field label:I\n",
        "field declaration", path,
    )

    # 1b. constructor signature
    src = sub_once(
        src,
        ".method constructor <init>(Lcom/leestone/stoneai/data/StudioUiState;"
        "Landroidx/compose/foundation/lazy/LazyListState;"
        "Lkotlin/coroutines/Continuation;)V\n",
        ".method constructor <init>(Lcom/leestone/stoneai/data/StudioUiState;"
        "Landroidx/compose/foundation/lazy/LazyListState;Z"
        "Lkotlin/coroutines/Continuation;)V\n",
        "constructor declaration", path,
    )

    # 1c. constructor Kotlin @Signature annotation
    src = sub_once(
        src,
        '            "Landroidx/compose/foundation/lazy/LazyListState;",\n'
        '            "Lkotlin/coroutines/Continuation<",\n',
        '            "Landroidx/compose/foundation/lazy/LazyListState;",\n'
        '            "Z",\n'
        '            "Lkotlin/coroutines/Continuation<",\n',
        "constructor signature annotation", path,
    )

    # 1d. constructor body
    src = sub_once(
        src,
        "    iput-object p2, p0, %s->$listState:Landroidx/compose/foundation/lazy/LazyListState;\n"
        "\n"
        "    const/4 v0, 0x2\n"
        "\n"
        "    invoke-direct {p0, v0, p3}, Lkotlin/coroutines/jvm/internal/SuspendLambda;-><init>(ILkotlin/coroutines/Continuation;)V\n" % LAMBDA,
        "    iput-object p2, p0, %s->$listState:Landroidx/compose/foundation/lazy/LazyListState;\n"
        "\n"
        "    iput-boolean p3, p0, %s->$atBottom:Z\n"
        "\n"
        "    const/4 v0, 0x2\n"
        "\n"
        "    invoke-direct {p0, v0, p4}, Lkotlin/coroutines/jvm/internal/SuspendLambda;-><init>(ILkotlin/coroutines/Continuation;)V\n" % (LAMBDA, LAMBDA),
        "constructor body", path,
    )

    # 1e. create(): one more register for the extra captured value
    src = sub_once(
        src,
        ".method public final create(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)"
        "Lkotlin/coroutines/Continuation;\n"
        "    .locals 3\n",
        ".method public final create(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)"
        "Lkotlin/coroutines/Continuation;\n"
        "    .locals 4\n",
        "create() locals", path,
    )

    # 1f. create(): copy the flag into the coroutine continuation clone
    src = sub_once(
        src,
        "    iget-object v2, p0, %s->$listState:Landroidx/compose/foundation/lazy/LazyListState;\n"
        "\n"
        "    invoke-direct {v0, v1, v2, p2}, %s-><init>(Lcom/leestone/stoneai/data/StudioUiState;"
        "Landroidx/compose/foundation/lazy/LazyListState;Lkotlin/coroutines/Continuation;)V\n" % (LAMBDA, LAMBDA),
        "    iget-object v2, p0, %s->$listState:Landroidx/compose/foundation/lazy/LazyListState;\n"
        "\n"
        "    iget-boolean v3, p0, %s->$atBottom:Z\n"
        "\n"
        "    invoke-direct {v0, v1, v2, v3, p2}, %s-><init>(Lcom/leestone/stoneai/data/StudioUiState;"
        "Landroidx/compose/foundation/lazy/LazyListState;Z"
        "Lkotlin/coroutines/Continuation;)V\n" % (LAMBDA, LAMBDA, LAMBDA),
        "create() body", path,
    )

    # 1g. invokeSuspend(): don't touch the list unless the user is at the bottom
    src = sub_once(
        src,
        "    invoke-interface {v1}, Ljava/util/Collection;->isEmpty()Z\n"
        "\n"
        "    move-result v1\n"
        "\n"
        "    if-nez v1, :cond_1\n",
        "    invoke-interface {v1}, Ljava/util/Collection;->isEmpty()Z\n"
        "\n"
        "    move-result v1\n"
        "\n"
        "    if-nez v1, :cond_1\n"
        "\n"
        "    iget-boolean v1, p0, %s->$atBottom:Z\n"
        "\n"
        "    if-eqz v1, :cond_1\n" % LAMBDA,
        "invokeSuspend() guard", path,
    )

    # 1h. jump straight to the bottom instead of animating (an animation is
    #     restarted on every token and never settles, which is what fights the user)
    src = sub_once(
        src,
        "    invoke-static/range {v2 .. v7}, Landroidx/compose/foundation/lazy/LazyListState;->"
        "animateScrollToItem$default(Landroidx/compose/foundation/lazy/LazyListState;II"
        "Lkotlin/coroutines/Continuation;ILjava/lang/Object;)Ljava/lang/Object;\n",
        "    invoke-static/range {v2 .. v7}, Landroidx/compose/foundation/lazy/LazyListState;->"
        "scrollToItem$default(Landroidx/compose/foundation/lazy/LazyListState;II"
        "Lkotlin/coroutines/Continuation;ILjava/lang/Object;)Ljava/lang/Object;\n",
        "scroll call", path,
    )

    open(path, "w", encoding="utf-8").write(src)
    print("patched %s" % path)


# --------------------------------------------------------------------------
# 2. ChatScreenKt (the composable): build the lambda through a small helper
#    that snapshots listState.canScrollForward at composition time.
# --------------------------------------------------------------------------

def patch_screen(path):
    src = open(path, encoding="utf-8").read()

    src = sub_once(
        src,
        "    new-instance v13, %s\n"
        "\n"
        "    move/from16 v21, v15\n" % LAMBDA,
        "    move/from16 v21, v15\n",
        "lambda instantiation", path,
    )

    src = sub_once(
        src,
        "    invoke-direct {v13, v0, v8, v15}, %s-><init>(Lcom/leestone/stoneai/data/StudioUiState;"
        "Landroidx/compose/foundation/lazy/LazyListState;Lkotlin/coroutines/Continuation;)V\n" % LAMBDA,
        "    invoke-static {v0, v8, v15}, Lcom/leestone/stoneai/ui/ChatScrollSupport;->"
        "createChatScrollEffect(Lcom/leestone/stoneai/data/StudioUiState;"
        "Landroidx/compose/foundation/lazy/LazyListState;"
        "Lkotlin/coroutines/Continuation;)"
        "Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;\n"
        "\n"
        "    move-result-object v13\n",
        "lambda constructor call", path,
    )

    open(path, "w", encoding="utf-8").write(src)
    print("patched %s" % path)


# --------------------------------------------------------------------------
# 3. New helper class
# --------------------------------------------------------------------------

SUPPORT_SMALI = """.class public final Lcom/leestone/stoneai/ui/ChatScrollSupport;
.super Ljava/lang/Object;
.source "ChatScrollSupport.kt"


# direct methods
.method public static final createChatScrollEffect(Lcom/leestone/stoneai/data/StudioUiState;Landroidx/compose/foundation/lazy/LazyListState;Lkotlin/coroutines/Continuation;)Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;
    .locals 2

    new-instance v0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;

    invoke-virtual {p1}, Landroidx/compose/foundation/lazy/LazyListState;->getCanScrollForward()Z

    move-result v1

    xor-int/lit8 v1, v1, 0x1

    invoke-direct {v0, p0, p1, v1, p2}, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;-><init>(Lcom/leestone/stoneai/data/StudioUiState;Landroidx/compose/foundation/lazy/LazyListState;ZLkotlin/coroutines/Continuation;)V

    return-object v0
.end method
"""


def add_support(path):
    if os.path.exists(path):
        print("already present: %s" % path)
        return
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(SUPPORT_SMALI)
    print("created %s" % path)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    root = sys.argv[1]
    for rel in (EFFECT, SCREEN):
        if not os.path.exists(os.path.join(root, rel)):
            raise SystemExit("ERROR: %s not found under %s" % (rel, root))
    patch_effect(os.path.join(root, EFFECT))
    patch_screen(os.path.join(root, SCREEN))
    add_support(os.path.join(root, SUPPORT))
    print("done")


if __name__ == "__main__":
    main()
