.class final Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;
.super Lkotlin/coroutines/jvm/internal/SuspendLambda;
.source "ChatScreen.kt"

# interfaces
.implements Lkotlin/jvm/functions/Function2;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/leestone/stoneai/ui/ChatScreenKt;->ChatScreen(Lcom/leestone/stoneai/data/StudioUiState;Lcom/leestone/stoneai/StudioViewModel;Lkotlin/jvm/functions/Function0;Landroidx/compose/runtime/Composer;I)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x18
    name = null
.end annotation

.annotation system Ldalvik/annotation/Signature;
    value = {
        "Lkotlin/coroutines/jvm/internal/SuspendLambda;",
        "Lkotlin/jvm/functions/Function2<",
        "Lkotlinx/coroutines/CoroutineScope;",
        "Lkotlin/coroutines/Continuation<",
        "-",
        "Lkotlin/Unit;",
        ">;",
        "Ljava/lang/Object;",
        ">;"
    }
.end annotation

.annotation runtime Lkotlin/Metadata;
    d1 = {
        "\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"
    }
    d2 = {
        "<anonymous>",
        "",
        "Lkotlinx/coroutines/CoroutineScope;"
    }
    k = 0x3
    mv = {
        0x2,
        0x3,
        0x0
    }
    xi = 0x30
.end annotation

.annotation runtime Lkotlin/coroutines/jvm/internal/DebugMetadata;
    c = "com.leestone.stoneai.ui.ChatScreenKt$ChatScreen$1$1"
    f = "ChatScreen.kt"
    i = {}
    l = {
        0x49
    }
    m = "invokeSuspend"
    n = {}
    nl = {
        0x4a
    }
    s = {}
    v = 0x2
.end annotation


# instance fields
.field final synthetic $listState:Landroidx/compose/foundation/lazy/LazyListState;

.field final synthetic $state:Lcom/leestone/stoneai/data/StudioUiState;

.field final synthetic $atBottom:Z

.field label:I


# direct methods
.method constructor <init>(Lcom/leestone/stoneai/data/StudioUiState;Landroidx/compose/foundation/lazy/LazyListState;ZLkotlin/coroutines/Continuation;)V
    .locals 1
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Lcom/leestone/stoneai/data/StudioUiState;",
            "Landroidx/compose/foundation/lazy/LazyListState;",
            "Z",
            "Lkotlin/coroutines/Continuation<",
            "-",
            "Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;",
            ">;)V"
        }
    .end annotation

    iput-object p1, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$state:Lcom/leestone/stoneai/data/StudioUiState;

    iput-object p2, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$listState:Landroidx/compose/foundation/lazy/LazyListState;

    iput-boolean p3, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$atBottom:Z

    const/4 v0, 0x2

    invoke-direct {p0, v0, p4}, Lkotlin/coroutines/jvm/internal/SuspendLambda;-><init>(ILkotlin/coroutines/Continuation;)V

    return-void
.end method


# virtual methods
.method public final create(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Lkotlin/coroutines/Continuation;
    .locals 4
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Ljava/lang/Object;",
            "Lkotlin/coroutines/Continuation<",
            "*>;)",
            "Lkotlin/coroutines/Continuation<",
            "Lkotlin/Unit;",
            ">;"
        }
    .end annotation

    new-instance v0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;

    iget-object v1, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$state:Lcom/leestone/stoneai/data/StudioUiState;

    iget-object v2, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$listState:Landroidx/compose/foundation/lazy/LazyListState;

    iget-boolean v3, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$atBottom:Z

    invoke-direct {v0, v1, v2, v3, p2}, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;-><init>(Lcom/leestone/stoneai/data/StudioUiState;Landroidx/compose/foundation/lazy/LazyListState;ZLkotlin/coroutines/Continuation;)V

    check-cast v0, Lkotlin/coroutines/Continuation;

    return-object v0
.end method

.method public bridge synthetic invoke(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    .locals 1

    check-cast p1, Lkotlinx/coroutines/CoroutineScope;

    check-cast p2, Lkotlin/coroutines/Continuation;

    invoke-virtual {p0, p1, p2}, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->invoke(Lkotlinx/coroutines/CoroutineScope;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;

    move-result-object v0

    return-object v0
.end method

.method public final invoke(Lkotlinx/coroutines/CoroutineScope;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;
    .locals 2
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Lkotlinx/coroutines/CoroutineScope;",
            "Lkotlin/coroutines/Continuation<",
            "-",
            "Lkotlin/Unit;",
            ">;)",
            "Ljava/lang/Object;"
        }
    .end annotation

    invoke-virtual {p0, p1, p2}, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->create(Ljava/lang/Object;Lkotlin/coroutines/Continuation;)Lkotlin/coroutines/Continuation;

    move-result-object v0

    check-cast v0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;

    sget-object v1, Lkotlin/Unit;->INSTANCE:Lkotlin/Unit;

    invoke-virtual {v0, v1}, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->invokeSuspend(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v0

    return-object v0
.end method

.method public final invokeSuspend(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 8
    .param p1, "$result"    # Ljava/lang/Object;

    invoke-static {}, Lkotlin/coroutines/intrinsics/IntrinsicsKt;->getCOROUTINE_SUSPENDED()Ljava/lang/Object;

    move-result-object v0

    .line 72
    iget v1, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->label:I

    packed-switch v1, :pswitch_data_0

    new-instance v0, Ljava/lang/IllegalStateException;

    const-string v1, "call to \'resume\' before \'invoke\' with coroutine"

    invoke-direct {v0, v1}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    throw v0

    :pswitch_0
    invoke-static {p1}, Lkotlin/ResultKt;->throwOnFailure(Ljava/lang/Object;)V

    goto :goto_0

    :pswitch_1
    invoke-static {p1}, Lkotlin/ResultKt;->throwOnFailure(Ljava/lang/Object;)V

    .line 73
    iget-object v1, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$state:Lcom/leestone/stoneai/data/StudioUiState;

    invoke-virtual {v1}, Lcom/leestone/stoneai/data/StudioUiState;->getMessages()Ljava/util/List;

    move-result-object v1

    check-cast v1, Ljava/util/Collection;

    invoke-interface {v1}, Ljava/util/Collection;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_1

    iget-boolean v1, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$atBottom:Z

    if-eqz v1, :cond_1

    iget-object v2, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$listState:Landroidx/compose/foundation/lazy/LazyListState;

    iget-object v1, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->$state:Lcom/leestone/stoneai/data/StudioUiState;

    invoke-virtual {v1}, Lcom/leestone/stoneai/data/StudioUiState;->getMessages()Ljava/util/List;

    move-result-object v1

    invoke-static {v1}, Lkotlin/collections/CollectionsKt;->getLastIndex(Ljava/util/List;)I

    move-result v3

    move-object v5, p0

    check-cast v5, Lkotlin/coroutines/Continuation;

    const/4 v1, 0x1

    iput v1, p0, Lcom/leestone/stoneai/ui/ChatScreenKt$ChatScreen$1$1;->label:I

    const/4 v4, 0x0

    const/4 v6, 0x2

    const/4 v7, 0x0

    invoke-static/range {v2 .. v7}, Landroidx/compose/foundation/lazy/LazyListState;->scrollToItem$default(Landroidx/compose/foundation/lazy/LazyListState;IILkotlin/coroutines/Continuation;ILjava/lang/Object;)Ljava/lang/Object;

    move-result-object v1

    if-ne v1, v0, :cond_0

    .line 72
    return-object v0

    .line 74
    :cond_0
    :goto_0
    nop

    :cond_1
    sget-object v0, Lkotlin/Unit;->INSTANCE:Lkotlin/Unit;

    return-object v0

    :pswitch_data_0
    .packed-switch 0x0
        :pswitch_1
        :pswitch_0
    .end packed-switch
.end method
