.class public final Lcom/leestone/stoneai/ui/ChatScrollSupport;
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
