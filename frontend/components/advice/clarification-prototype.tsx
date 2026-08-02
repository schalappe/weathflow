"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  CircleHelp,
  Link2,
  Pencil,
  Trash2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const variants = [
  { key: "A", name: "Étape focalisée" },
  { key: "B", name: "Conseil progressif" },
  { key: "C", name: "Preuves côte à côte" },
] as const;

type VariantKey = (typeof variants)[number]["key"];
type Answer = "rent" | "savings" | "skipped" | null;

interface VariantProps {
  answer: Answer;
  remember: boolean;
  onAnswer: (answer: Exclude<Answer, null>) => void;
  onRememberChange: () => void;
  onCorrect: () => void;
}

function QuestionReason() {
  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
        <div>
          <p className="font-medium">Incertitude détectée</p>
          <p className="text-muted-foreground">
            Un virement de 850 € vers SCI BELLECOUR revient chaque mois, mais
            son libellé ne dit pas s’il s’agit d’une charge ou d’épargne.
          </p>
        </div>
      </div>
      <div className="flex items-start gap-3">
        <CircleHelp className="mt-0.5 size-4 shrink-0 text-primary" />
        <div>
          <p className="font-medium">Pourquoi cette question ?</p>
          <p className="text-muted-foreground">
            La réponse change votre marge mensuelle de 850 € et donc le conseil
            sur votre trajectoire d’épargne.
          </p>
        </div>
      </div>
    </div>
  );
}

function AnswerButtons({ onAnswer }: Pick<VariantProps, "onAnswer">) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Button
        variant="outline"
        className="h-auto justify-start whitespace-normal p-4 text-left"
        onClick={() => onAnswer("rent")}
      >
        C’est mon loyer
      </Button>
      <Button
        variant="outline"
        className="h-auto justify-start whitespace-normal p-4 text-left"
        onClick={() => onAnswer("savings")}
      >
        C’est un virement vers mon épargne
      </Button>
    </div>
  );
}

function AdviceOutcome({ answer }: { answer: Answer }) {
  if (answer === "rent") {
    return (
      <div className="space-y-2">
        <Badge>Priorité ajustée</Badge>
        <h3 className="text-lg font-semibold">
          Constituez d’abord une marge de sécurité
        </h3>
        <p className="text-sm text-muted-foreground">
          Votre loyer laisse environ 360 € de marge mensuelle. Visez 180 € par
          mois pour le fonds d’urgence avant d’augmenter un autre objectif.
        </p>
      </div>
    );
  }

  if (answer === "savings") {
    return (
      <div className="space-y-2">
        <Badge>Aucune hausse nécessaire</Badge>
        <h3 className="text-lg font-semibold">
          Votre trajectoire est déjà suffisante
        </h3>
        <p className="text-sm text-muted-foreground">
          Les 850 € mensuels sont déjà de l’épargne. Maintenez ce rythme ; les
          données disponibles ne justifient pas de l’augmenter.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Badge variant="outline">Sujet non conclu</Badge>
      <h3 className="text-lg font-semibold">
        Trajectoire d’épargne non chiffrée
      </h3>
      <p className="text-sm text-muted-foreground">
        Si ce virement est un loyer, la marge est limitée ; s’il alimente votre
        épargne, votre objectif est déjà couvert. Aucune action n’est priorisée.
      </p>
    </div>
  );
}

function ContextControls({
  answer,
  remember,
  onRememberChange,
  onCorrect,
}: Pick<
  VariantProps,
  "answer" | "remember" | "onRememberChange" | "onCorrect"
>) {
  if (answer !== "rent" && answer !== "savings") return null;

  const fact =
    answer === "rent" ? "Loyer mensuel · 850 €" : "Épargne mensuelle · 850 €";

  return (
    <div className="space-y-3 rounded-lg border bg-muted/30 p-4 text-sm">
      <div className="flex items-center gap-2 font-medium">
        <Link2 className="size-4 text-primary" />
        Ce conseil utilise votre réponse
      </div>
      <p>{fact}</p>
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={onRememberChange}>
          {remember && <Check className="size-3" />}
          {remember ? "Réutiliser plus tard" : "Cette fois seulement"}
        </Button>
        <Button variant="ghost" size="sm" onClick={onCorrect}>
          <Pencil className="size-3" />
          Corriger
        </Button>
        <Button variant="ghost" size="sm" onClick={onCorrect}>
          <Trash2 className="size-3" />
          Supprimer
        </Button>
      </div>
    </div>
  );
}

function StateStrip({
  answer,
  remember,
}: Pick<VariantProps, "answer" | "remember">) {
  const label =
    answer === null
      ? "Question active · aucun conseil dépendant affiché"
      : answer === "skipped"
        ? "Question passée · sujet non conclu"
        : `Réponse utilisée · ${remember ? "fait mémorisé" : "réponse de session"}`;

  return (
    <div
      aria-live="polite"
      className="rounded-md border border-dashed px-3 py-2 text-xs text-muted-foreground"
    >
      État simulé : {label}
    </div>
  );
}

function VariantA(props: VariantProps) {
  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div className="text-center">
        <Badge variant="secondary">Clarification 1 sur 3 maximum</Badge>
        <h1 className="mt-4 text-2xl font-bold">
          Une question avant votre conseil
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Une seule réponse peut changer la recommandation principale.
        </p>
      </div>
      {props.answer === null ? (
        <Card className="shadow-lg">
          <CardContent className="space-y-6 pt-6">
            <QuestionReason />
            <Separator />
            <div className="space-y-3">
              <h2 className="font-semibold">À quoi correspond ce virement ?</h2>
              <AnswerButtons onAnswer={props.onAnswer} />
              <Button
                variant="ghost"
                className="w-full"
                onClick={() => props.onAnswer("skipped")}
              >
                Passer
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="shadow-lg">
          <CardContent className="space-y-5 pt-6">
            <AdviceOutcome answer={props.answer} />
            <ContextControls {...props} />
            {props.answer === "skipped" && (
              <Button variant="outline" onClick={props.onCorrect}>
                Répondre maintenant
              </Button>
            )}
          </CardContent>
        </Card>
      )}
      <StateStrip answer={props.answer} remember={props.remember} />
    </div>
  );
}

function VariantB(props: VariantProps) {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Votre conseil de juillet</h1>
        <p className="text-muted-foreground">
          Les conclusions sûres restent visibles pendant la clarification.
        </p>
      </div>
      <Card>
        <CardContent className="space-y-6 pt-6">
          <section className="space-y-2">
            <Badge variant="secondary">Recommandation robuste</Badge>
            <h2 className="font-semibold">
              Résiliez l’assurance mobile en double
            </h2>
            <p className="text-sm text-muted-foreground">
              Deux prélèvements couvrent le même téléphone. Économie observée :
              18 € par mois.
            </p>
          </section>
          <Separator />
          {props.answer === null ? (
            <section className="space-y-5 rounded-lg border border-amber-500/40 bg-amber-500/5 p-5">
              <QuestionReason />
              <div className="space-y-3">
                <h2 className="font-semibold">
                  À quoi correspond ce virement ?
                </h2>
                <AnswerButtons onAnswer={props.onAnswer} />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => props.onAnswer("skipped")}
                >
                  Passer ce sujet
                </Button>
              </div>
            </section>
          ) : (
            <section className="space-y-4">
              <AdviceOutcome answer={props.answer} />
              <ContextControls {...props} />
              {props.answer === "skipped" && (
                <Button variant="outline" size="sm" onClick={props.onCorrect}>
                  Répondre maintenant
                </Button>
              )}
            </section>
          )}
        </CardContent>
      </Card>
      <StateStrip answer={props.answer} remember={props.remember} />
    </div>
  );
}

function VariantC(props: VariantProps) {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Conseil et preuves</h1>
        <p className="text-muted-foreground">
          Chaque conclusion reste reliée à ce qui la justifie.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardContent className="space-y-6 pt-6">
            <section className="space-y-2">
              <Badge variant="secondary">Données observées</Badge>
              <h2 className="font-semibold">
                18 € d’assurance mobile en double
              </h2>
              <p className="text-sm text-muted-foreground">
                Résiliez le contrat le plus récent.
              </p>
            </section>
            <Separator />
            <section
              className={
                props.answer === null ? "space-y-3 opacity-45" : "space-y-3"
              }
            >
              {props.answer === null ? (
                <>
                  <Badge variant="outline">En attente d’un fait</Badge>
                  <h2 className="font-semibold">Trajectoire d’épargne</h2>
                  <p className="text-sm text-muted-foreground">
                    Cette recommandation reste masquée tant que la nature du
                    virement n’est pas connue.
                  </p>
                </>
              ) : (
                <AdviceOutcome answer={props.answer} />
              )}
            </section>
            <ContextControls {...props} />
          </CardContent>
        </Card>
        <aside className="space-y-4">
          <Card>
            <CardContent className="space-y-5 pt-6">
              <div>
                <Badge variant="outline">Source à confirmer</Badge>
                <h2 className="mt-3 font-semibold">Virement SCI BELLECOUR</h2>
              </div>
              {props.answer === null ? (
                <>
                  <QuestionReason />
                  <AnswerButtons onAnswer={props.onAnswer} />
                  <Button
                    variant="ghost"
                    className="w-full"
                    onClick={() => props.onAnswer("skipped")}
                  >
                    Passer
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    {props.answer === "skipped"
                      ? "Aucune réponse utilisée."
                      : "Réponse reliée à la recommandation affichée à gauche."}
                  </p>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={props.onCorrect}
                  >
                    <Pencil className="size-4" />
                    {props.answer === "skipped" ? "Répondre" : "Corriger"}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
          <StateStrip answer={props.answer} remember={props.remember} />
        </aside>
      </div>
    </div>
  );
}

function PrototypeSwitcher({ variant }: { variant: VariantKey }) {
  const router = useRouter();

  const move = useCallback(
    (offset: number) => {
      const index = variants.findIndex((item) => item.key === variant);
      const next =
        variants[(index + offset + variants.length) % variants.length];
      router.replace(`/advice?prototype=clarification&variant=${next.key}`);
    },
    [router, variant],
  );

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, [contenteditable]")) return;
      if (event.key === "ArrowLeft") move(-1);
      if (event.key === "ArrowRight") move(1);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [move]);

  if (process.env.NODE_ENV === "production") return null;

  const current = variants.find((item) => item.key === variant) ?? variants[0];

  return (
    <div className="fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full bg-foreground px-2 py-2 text-background shadow-xl">
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={() => move(-1)}
        aria-label="Variante précédente"
      >
        <ArrowLeft className="size-4" />
      </Button>
      <span className="min-w-48 text-center text-sm font-medium">
        {current.key} — {current.name}
      </span>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={() => move(1)}
        aria-label="Variante suivante"
      >
        <ArrowRight className="size-4" />
      </Button>
    </div>
  );
}

export function ClarificationPrototype({
  initialVariant,
}: {
  initialVariant?: string;
}) {
  const variant =
    variants.find((item) => item.key === initialVariant)?.key ?? "A";
  const [answer, setAnswer] = useState<Answer>(null);
  const [remember, setRemember] = useState(true);
  const props: VariantProps = {
    answer,
    remember,
    onAnswer: setAnswer,
    onRememberChange: () => setRemember((current) => !current),
    onCorrect: () => setAnswer(null),
  };

  return (
    <>
      {variant === "A" && <VariantA {...props} />}
      {variant === "B" && <VariantB {...props} />}
      {variant === "C" && <VariantC {...props} />}
      <PrototypeSwitcher variant={variant} />
    </>
  );
}
