import { Play } from "lucide-react";
import Link from "next/link";

import { RainbowText } from "~/components/core/rainbow-text";
import { Button } from "~/components/ui/button";
import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "~/components/ui/card";
import { cn } from "~/lib/utils";

export function ReplaysSection() {
    const replays = [
        { id: "test-case-720", title: "石墨原矿石碳品位视觉深度分析", date: "2025/5/19 12:54", category: "Academic", count: 1533 },
        // Placeholder for replays data
        { id: "ai-twin-insurance", title: "Write an article on \"Would you insure your AI twin?\"", date: "2025/5/19 12:54", category: "Social Media", count: 500 },
        { id: "china-food-delivery", title: "如何看待外卖大战", date: "2025/5/20 14:30", category: "Research", count: 1000 },
        //{ id: "eiffel-tower-vs-tallest-building", title: "How many times taller is the Eiffel Tower than the tallest building in the world?", date: "2025/5/21 16:45", category: "Technology", count: 8 },
        //{ id: "github-top-trending-repo", title: "Write a brief on the top 1 trending repo on Github today.", date: "2025/5/22 18:00", category: "Education", count: 120 },
        { id: "nanjing-traditional-dishes", title: "Write an article about Nanjing's traditional dishes.", date: "2025/5/23 20:15", category: "Health", count: 60 },
        //{ id: "rag-flow", title: "奔驰汽车如何更换玻璃水？", date: "2025/5/23 20:15", category: "Health", count: 89 },
        { id: "rental-apartment-decoration", title: "How to decorate a small rental apartment?", date: "2025/5/23 20:15", category: "Health", count: 116 },
        //{ id: "review-of-the-professional", title: "Introduce the movie 'Léon: The Professional'", date: "2025/5/23 20:15", category: "Health", count: 678 },
        { id: "ultra-processed-foods", title: "Are ultra-processed foods linked to health?", date: "2025/5/23 20:15", category: "Health", count: 600 },
    ]; // Placeholder for replays data
    return (
        <div className="flex flex-wrap w-full ">
            {replays.map((replay) => (
                <div key={replay.id} className="flex w-full sm:w-1/2 md:w-1/3 shrink-2 ">
                    <Card
                        className={cn(
                            "w-[98%] transition-all duration-300 pt-5 mt-5 rounded-2xl",
                        )}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex flex-grow items-center">

                                <CardHeader className={cn("flex-grow pl-3")}>
                                    <CardTitle>
                                        <RainbowText animated={false}>
                                            {`${replay.title}`}
                                        </RainbowText>
                                    </CardTitle>
                                    <CardDescription>
                                        <RainbowText animated={false}>
                                            {`${replay.date.substring(0, 19).replace(/-/g, "/").replace("T", " ")} | ${replay.category} | ${replay.count} messages`}
                                        </RainbowText>
                                    </CardDescription>
                                </CardHeader>
                            </div>
                            <div className="pr-4">
                                <Link href={`/chat?replay=${replay.id}${replay.date.includes("2025/5") ? `` : "&db=true"}`}>
                                    <Button className="w-24" variant="default" >
                                        <Play size={16} />
                                        Replay
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </Card>
                </div>
            ))}
        </div>
    );
}